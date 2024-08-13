from typing import Callable, Optional, Union

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend

try:
    from strapp.dramatiq.datadog import DatadogMiddleware
except Exception:  # nosec
    pass


def configure(
    *,
    redis_dsn=None,
    enable_datadog_middleware: bool = False,
    env: Optional[str] = None,
) -> RedisBroker:
    """Configure a Redis broker.

    Both the worker itself, as well as any code which wants to `enqueue` work, should call this
    function at startup.
    """

    backend = RedisBackend(url=redis_dsn)
    broker = RedisBroker(url=redis_dsn)
    broker.add_middleware(Results(backend=backend))

    if enable_datadog_middleware:
        broker.add_middleware(DatadogMiddleware(env=env))

    dramatiq.set_broker(broker)

    return broker


class PreparedActor:
    """Prepared configuration for a Dramatiq Actor.

    The default actor implementation does not require an explicit name and uses the function name
    by default. In order to safely use `enqueue` for tasks, being explicit about the name seems safer.

    Keep in mind that actor names must be globally unique.

    dramatiq default timeout is 10 minutes, but we default to 1 hour for greater flexibility.

    The default max_retries for dramatiq is 5, but we default to 0. If you notice your task
    failing due to transient network behavior then consider upping it and modifying backoff parameters.
    https://dramatiq.io/guide.html#message-retries
    """

    def __init__(
        self,
        fn: Callable,
        *,
        actor_name: Optional[str] = None,
        broker: dramatiq.Broker = None,
        queue_name: str = "default",
        store_results: bool = False,
        time_limit_ms: int = 1000 * 60 * 60,
        max_retries: Optional[int] = 0,
        **options,
    ):
        self.fn = fn
        self.actor_name = actor_name
        self.broker = broker
        self.queue_name = queue_name
        self.store_results = store_results
        self.time_limit_ms = time_limit_ms
        self.max_retries = max_retries
        self.options = options

    def register(self, broker: dramatiq.Broker = None) -> dramatiq.Actor:
        """Register an actor to a broker."""

        actor_decorator = dramatiq.actor(
            # arguments for dramatiq.Actor
            actor_name=self.actor_name or self.fn.__name__,
            broker=broker or self.broker,
            queue_name=self.queue_name,
            # options passed to middleware
            store_results=self.store_results,
            time_limit=self.time_limit_ms,
            max_retries=self.max_retries,
            **self.options,
        )

        return actor_decorator(self.fn)


def enqueue(
    task_name: str,
    *,
    queue_name="default",
    broker=None,
    pipe_target: Optional[dramatiq.Message] = None,
    pipe_ignore: bool = False,
    **kwargs,
) -> dramatiq.Message:
    """Enqueue work onto the queue, by `task_name`.

    The "default" behavior is to use the actual python function object `actor.send`. Given
    that we should strive to avoid the need to **have** a direct handle on the python function
    being enqueued, this `enqueue` function uses the actor name to target the actor.

    Args:
        task_name: The string name given to the `@actor` decorator.
        queue_name: optional queue name. defaults to "default".
        broker: Overrides the global broker
        pipe_target: Optional pipe target. This is used to chain tasks together.
        pipe_ignore: When True, ignores the result of the previous actor in the pipeline.
        **kwargs: Passed through to the corresponding `@actor` function. Must be json serializable.
    """
    if broker is None:
        broker = dramatiq.get_broker()

    m = message(
        task_name,
        queue_name=queue_name,
        pipe_target=pipe_target,
        pipe_ignore=pipe_ignore,
        **kwargs,
    )
    return broker.enqueue(m)


def message(
    task_name,
    *,
    queue_name="default",
    pipe_target: Optional[dramatiq.Message] = None,
    pipe_ignore: bool = False,
    **kwargs,
) -> dramatiq.Message:
    """Create a dramatiq message."""
    options = {}
    if pipe_target:
        options["pipe_target"] = pipe_target.asdict()

    if pipe_ignore:
        options["pipe_ignore"] = True

    return dramatiq.Message(
        queue_name=queue_name,
        actor_name=task_name,
        args=(),
        kwargs=kwargs,
        options=options,
    )


def get_result(
    task_name_or_message: Union[str, dramatiq.Message] = None,
    message_id=None,
    *,
    queue_name="default",
    block: bool = False,
    timeout: Optional[int] = None,
):
    """Get the result from an actor which stores results.

    Arguments:
        task_name_or_message: The first argument should be either the message returned by the original, `enqueue`
            call, or the task name of the task for which you want results.
        message_id: The message_id would have been directly available on the result of an `enqueue` call,
            by its `message_id` attribute.
        queue_name: Optional queue name. defaults to "default".
        block: Whether or not to block while waiting for a
            result.
        timeout: The maximum amount of time, in ms, to block while waiting for a result.

    Examples:
        Define an actor
        >>> def task_name():                                # doctest: +SKIP
        ...     return True
        >>> PreparedActor(task_name, store_results=True)    # doctest: +SKIP

        Enqueue a task
        >>> message = enqueue('task_name')                  # doctest: +SKIP
        >>> message_id = message.message_id                 # doctest: +SKIP

        # Option 1
        >>> get_result(message)                             # doctest: +SKIP
        True

        # Option 2
        >>> get_result('task_name', message_id)             # doctest: +SKIP
        True
    """
    if isinstance(task_name_or_message, dramatiq.Message):
        message = task_name_or_message
    else:
        message = dramatiq.Message(
            queue_name=queue_name,
            actor_name=task_name_or_message,
            message_id=message_id,
            args=(),
            kwargs={},
            options={},
        )

    return message.get_result(block=block, timeout=timeout)

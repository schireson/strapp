import dramatiq

from strapp.dramatiq.base import enqueue, get_result, PreparedActor
from strapp.dramatiq.testing import worker_context


def foo():
    return "bar"


task = PreparedActor(foo, store_results=True)


def test_e2e(e2e_broker):
    task.register(e2e_broker)

    with worker_context(e2e_broker):
        message = enqueue("foo")
        task_id = message.message_id

    result = get_result("foo", task_id, timeout=5)
    assert result == "bar"


def test_e2e_alt(e2e_broker):
    task.register(e2e_broker)

    with worker_context(e2e_broker):
        message = enqueue("foo", broker=e2e_broker)
        task_id = message.message_id

    message = dramatiq.Message(
        queue_name="default",
        actor_name="foo",
        message_id=task_id,
        # required kwargs to dramatiq.Message
        args=(),
        kwargs={},
        options={},
    )
    result = get_result(message, timeout=5)
    assert result == "bar"

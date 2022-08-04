import dramatiq
from dramatiq.middleware import Middleware

try:
    import sentry_sdk
except ImportError:
    raise RuntimeError("sentry_sdk is not installed.")


class SentryMiddleware(Middleware):
    def __init__(self, *, sentry_sdk=sentry_sdk):
        self.sentry_sdk = sentry_sdk

    def before_process_message(self, broker: dramatiq.Broker, message: dramatiq.Message):
        with self.sentry_sdk.configure_scope() as scope:
            scope.set_tag("queue_name", message.queue_name)
            scope.set_tag("actor_name", message.actor_name)
            scope.set_tag("message_id", message.message_id)
            scope.set_context("task args", dict(enumerate(message.args)))  # cannot be list
            scope.set_context("task kwargs", message.kwargs)
            scope.set_context("task options", message.options)

    def after_process_message(
        self, broker: dramatiq.Broker, message: dramatiq.Message, *, result=None, exception=None
    ):
        if exception is not None:
            self.sentry_sdk.capture_exception(exception)

        with self.sentry_sdk.configure_scope() as scope:
            scope.clear()

import time

from dramatiq.middleware import Middleware

try:
    from strapp.datadog import gauge, increment
except ImportError:
    raise RuntimeError("strapp.datadog is required for datadog middleware")


class DatadogMiddleware(Middleware):
    def __init__(self, *, env=None, increment=increment, gauge=gauge):
        self.env = env
        self.increment = increment
        self.gauge = gauge

        self.message_start_times = {}

    def tags(self, broker, message):
        return [
            f"queue_name:{message.queue_name}",
            f"actor_name:{message.actor_name}",
            f"broker_id:{broker.broker_id}",
            f"env:{self.env}",
        ]

    def before_enqueue(self, broker, message, delay):
        if "retries" in message.options:
            return

        tags = self.tags(broker, message)
        self.increment("dramatiq.message.requested", tags=tags)

    def after_ack(self, broker, message):
        tags = self.tags(broker, message)
        self.increment("dramatiq.message.completed", tags=tags)

    def after_nack(self, broker, message):
        tags = self.tags(broker, message)
        self.increment("dramatiq.message.rejected", tags=tags)

    def after_enqueue(self, broker, message, delay):
        tags = self.tags(broker, message)
        if "retries" in message.options:
            self.increment("dramatiq.message.retried", tags=tags)
        else:
            self.increment("dramatiq.message.enqueued", tags=tags)

    def before_process_message(self, broker, message):
        tags = self.tags(broker, message)
        self.increment("dramatiq.message.inprogress", tags=tags)
        self.message_start_times[message.message_id] = _current_millis()

    def after_process_message(self, broker, message, *, result=None, exception=None):
        tags = self.tags(broker, message)
        message_start_time = self.message_start_times.pop(message.message_id, _current_millis())
        message_duration = _current_millis() - message_start_time

        self.gauge("dramatiq.message.duration", message_duration, tags=tags)
        self.increment("dramatiq.message.inprogress", tags=tags, value=-1)
        self.increment("dramatiq.message.total", tags=tags)
        if exception is not None:
            self.increment("dramatiq.message.failed", tags=tags)


def _current_millis():
    return int(time.time() * 1000)

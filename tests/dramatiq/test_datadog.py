import pytest
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import Retries, TimeLimit
from dramatiq.results import Results
from dramatiq.results.backends import StubBackend
from dramatiq.worker import Worker
from freezegun import freeze_time

from strapp.dramatiq.base import enqueue, PreparedActor
from strapp.dramatiq.datadog import DatadogMiddleware


@pytest.fixture()
def broker():
    increments = {}
    gauges = {}

    def increment(metric, value=1, tags=None):
        if metric not in increments:
            increments[metric] = 0
        increments[metric] += value

    def gauge(metric, value, tags=None):
        if metric not in gauges:
            gauges[metric] = 0
        gauges[metric] += value

    broker = StubBroker(
        [
            Results(backend=StubBackend()),
            TimeLimit(),
            Retries(),
            DatadogMiddleware(increment=increment, gauge=gauge),
        ]
    )
    broker.broker_id = "4"

    broker.increments = increments
    broker.gauges = gauges

    yield broker
    broker.flush_all()
    broker.close()


@pytest.fixture()
def worker(broker):
    worker = Worker(broker, worker_timeout=100, worker_threads=32)
    worker.start()
    yield worker
    worker.stop()


class TestDatadogMiddleware:
    @freeze_time("2020-01-01", auto_tick_seconds=1)
    def test_successful_message(self, worker, broker):
        def do_work():
            pass

        PreparedActor(do_work, actor_name="foo").register(broker)

        enqueue("foo", broker=broker)
        enqueue("foo", broker=broker)

        broker.join("default")
        worker.join()

        assert broker.increments == {
            "dramatiq.message.requested": 2,
            "dramatiq.message.completed": 2,
            "dramatiq.message.enqueued": 2,
            "dramatiq.message.total": 2,
            "dramatiq.message.inprogress": 0,
        }
        assert broker.gauges["dramatiq.message.duration"] > 0

    def test_unsuccessful_message(self, worker, broker):
        def do_work():
            raise Exception()

        PreparedActor(do_work, actor_name="foo", max_retries=2, max_backoff=0).register(broker)

        enqueue("foo", broker=broker)
        enqueue("foo", broker=broker)

        broker.join("default")
        worker.join()

        assert broker.increments == {
            "dramatiq.message.completed": 8,
            "dramatiq.message.requested": 2,
            "dramatiq.message.enqueued": 2,
            "dramatiq.message.total": 6,
            "dramatiq.message.inprogress": 0,
            "dramatiq.message.rejected": 2,
            "dramatiq.message.failed": 6,
            "dramatiq.message.retried": 8,
        }
        assert broker.gauges["dramatiq.message.duration"] > 0

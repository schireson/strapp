import dramatiq
import pytest
from dramatiq.brokers.stub import StubBroker
from dramatiq.results import Results
from dramatiq.results.backends import StubBackend
from pytest_mock_resources import create_redis_fixture

from strapp.dramatiq import configure

redis = create_redis_fixture()


@pytest.fixture()
def e2e_broker(redis):
    url = redis.pmr_credentials.as_sqlalchemy_url()
    e2e_broker = configure(redis_dsn=str(url))

    dramatiq.set_broker(e2e_broker)

    e2e_broker.emit_after("process_boot")
    e2e_broker.flush_all()

    yield e2e_broker


@pytest.fixture()
def broker():
    backend = StubBackend()
    broker = StubBroker()
    broker.add_middleware(Results(backend=backend))

    dramatiq.set_broker(broker)

    broker.emit_after("process_boot")
    broker.flush_all()

    yield broker

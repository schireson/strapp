import os
import unittest.mock

import dramatiq
import pytest
import sentry_sdk
from dramatiq.middleware.time_limit import TimeLimitExceeded
from dramatiq.results.errors import ResultFailure

from strapp.dramatiq import enqueue, get_result, PreparedActor
from strapp.dramatiq.sentry import SentryMiddleware
from strapp.dramatiq.testing import worker_context


def sample_actor(num=5):
    if num > 5:
        raise ValueError("num is too big")
    return 5


def setup_mock_actor(fn, broker, retries=0) -> dramatiq.Actor:
    # Because python doesn't provide better way to spy on dynamicly declared functions ¯\_(ツ)_/¯
    mock = unittest.mock.Mock(fn)
    mock.side_effect = fn
    mock.__name__ = fn.__name__

    actor = PreparedActor(mock, max_retries=retries, max_backoff=1, store_results=True)

    return actor.register(broker=broker)


@pytest.mark.parametrize("retries", [0, 1, 2])
def test_retries(broker, retries):
    """Validate that retries are handled correctly."""
    actor = setup_mock_actor(sample_actor, broker, retries=retries)

    with pytest.raises(ValueError):
        with worker_context(broker, actor):
            message = enqueue("sample_actor", num=6)

    assert actor.fn.call_count == retries + 1  # n retries + 1 original call

    with pytest.raises(ResultFailure):
        get_result("sample_actor", message.message_id, timeout=0)


@pytest.mark.parametrize("exception_type", [ValueError, TimeLimitExceeded])
@unittest.mock.patch("strapp.dramatiq.sentry.sentry_sdk", autospec=True)
def test_sentry_middleware(mock_sentry_sdk, exception_type, broker):
    """Validate Sentry Middleware captures different kinds of exceptions and interrupts."""
    broker.add_middleware(SentryMiddleware(sentry_sdk=mock_sentry_sdk))

    def foo():
        raise exception_type()

    actor = PreparedActor(foo).register(broker)

    with pytest.raises(exception_type):
        with worker_context(broker, actor):
            enqueue("foo")

    assert mock_sentry_sdk.capture_exception.call_count == 1


@pytest.mark.skipif(os.environ.get("SENTRY_DSN") is None, reason="SENTRY_DSN is not set")
def test_sentry_middleware_live(broker):
    """Validate Sentry Middleware properly sends context details to the real Sentry."""
    import strapp.sentry

    strapp.sentry.setup_sentry(
        environment="test",
        service_name="tests.dramatiq.test_failures",
        dsn=os.getenv("SENTRY_DSN"),
    )

    broker.add_middleware(SentryMiddleware())

    actor = setup_mock_actor(sample_actor, broker, retries=0)

    with pytest.raises(ValueError):
        with worker_context(broker, actor):
            enqueue("sample_actor", num=6)

    sentry_sdk.flush()

    assert actor.fn.call_count == 1

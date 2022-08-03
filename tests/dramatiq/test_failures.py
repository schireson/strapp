import unittest.mock
from typing import Callable

import dramatiq
import pytest
from dramatiq.results.errors import ResultFailure

from strapp.dramatiq import enqueue, get_result, PreparedActor
from strapp.dramatiq.testing import worker_context


def setup_mock_actor(broker, retries=0) -> dramatiq.Actor:
    def sample_actor(num=5):
        if num > 5:
            raise ValueError("num is too big")
        return 5

    # Because python doesn't provide better way to spy on dynamicly declared functions ¯\_(ツ)_/¯
    mock = unittest.mock.Mock(sample_actor)
    mock.side_effect = sample_actor
    mock.__name__ = "sample_actor"

    actor = PreparedActor(mock, max_retries=retries, max_backoff_ms=1, store_results=True)

    return actor.register(broker=broker)


def test_retry(broker):
    actor = setup_mock_actor(broker, retries=3)

    with pytest.raises(ValueError):
        with worker_context(broker, actor):
            message = enqueue("sample_actor", num=6)

    assert actor.fn.call_count == 4  # 3 retries + 1 original call

    with pytest.raises(ResultFailure):
        get_result("sample_actor", message.message_id, timeout=0)

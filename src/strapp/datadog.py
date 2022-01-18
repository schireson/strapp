import contextlib
import datetime
import functools
import logging
from typing import Any, Dict, Optional, Union

import datadog
from configly import Config

log = logging.getLogger(__name__)


def setup(
    config: Union[Config, Dict[str, Any]],
    *,
    environment: Optional[str] = None,
    namespace: Optional[str] = None,
):
    app_key = config.get("app_key")
    api_key = config.get("app_key")
    statsd_host = config.get("statsd_host")
    statsd_port = config.get("statsd_port")

    if app_key is not None and api_key is not None:
        constant_tags = []

        if environment:
            constant_tags.append(f"environment:{environment}")

        datadog.initialize(
            api_key=api_key,
            app_key=app_key,
            statsd_host=statsd_host,
            statsd_port=statsd_port,
            statsd_constant_tags=constant_tags,
            statsd_namespace=namespace,
            hostname_from_config=False,
        )


def require_datadog_initialization(fn):
    @functools.wraps(fn)
    def decorator(*args, **kwargs):
        if datadog.api._api_key is not None and datadog.api._application_key is not None:
            fn(*args, **kwargs)

    return decorator


@require_datadog_initialization
def increment(metric, value=1, tags=None, sample_rate=None):
    datadog.statsd.increment(metric=metric, value=value, tags=tags, sample_rate=sample_rate)


@require_datadog_initialization
def gauge(metric, value, tags=None, sample_rate=None):
    datadog.statsd.gauge(metric=metric, value=value, tags=tags, sample_rate=sample_rate)


@contextlib.contextmanager
def gauge_duration(metric, tags=None, sample_rate=None):
    start = datetime.datetime.now()
    yield
    end = datetime.datetime.now()
    delta: datetime.timedelta = end - start

    gauge(metric, value=delta.seconds, tags=tags, sample_rate=sample_rate)

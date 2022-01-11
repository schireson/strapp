import contextlib
import datetime
import functools
import logging

import datadog
from configly import Config

log = logging.getLogger(__name__)


def setup(config: Config):
    if config.datadog.app_key is not None and config.datadog.api_key is not None:
        datadog.initialize(
            api_key=config.datadog.api_key,
            app_key=config.datadog.app_key,
            statsd_host=config.datadog.statsd_host,
            statsd_port=config.datadog.statsd_port,
            statsd_constant_tags=[f"environment:{config.environment}"],
            statsd_namespace="media_activation",
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

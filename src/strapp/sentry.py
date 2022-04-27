import contextlib
import json
import logging
import urllib.parse
from typing import Any, Dict, Optional, Union

import requests
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

log = logging.getLogger(__name__)


def setup_sentry(
    dsn,
    environment=None,
    service_name=None,
    level="WARNING",
    breadcrumb_level="INFO",
    **kwargs,
):
    """Initialize sentry.

    It's expected that this function is called once at app startup.
    """
    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            LoggingIntegration(level=breadcrumb_level, event_level=level),
            SqlalchemyIntegration(),
        ],
        attach_stacktrace=True,
        environment=environment,
        server_name=service_name,
        **kwargs,
    )


@contextlib.contextmanager
def add_context(*, user: Optional[Dict] = None, extra: Optional[Dict[str, Any]] = None, **tags):
    """Add extra context into any captured sentry events.

    Args:
        user: Sets the context's user.
        extra: Add extra non-indexed key/value pairs to the event.
        **tags: Add indexed key/value pairs to the event.

    Examples:
        Tags show up in sentry as tags/pills at the top of the issue to provide context. Furthermore
        They're indexed, and are therefore searchable.

        >>> with add_context(domain_model_id=4, report_type='foo'):
        ...     # Captured sentry events, such as unhandled exceptions will have these attributes
        ...     1 / 0
        Traceback (most recent call last):
          ...
        ZeroDivisionError: division by zero

        Sentry has an explicit notion of a "user", which is handled separately from other context.

        >>> with add_context(user={id: 1}):
        ...     1 / 0
        Traceback (most recent call last):
          ...
        ZeroDivisionError: division by zero

        Extras show up in sentry as extra, non-critical data towards the botton of the issue. They
        just provide additional context, and are not indexed.

        >>> with add_context(extra={'json': 1}):
        ...     1 / 0
        Traceback (most recent call last):
          ...
        ZeroDivisionError: division by zero
    """
    with sentry_sdk.push_scope() as scope:
        for name, value in tags.items():
            log.debug("Sentry: Tag(%s=%s)", name, value)
            scope.set_tag(name, value)

        if user is not None:
            log.debug("Sentry: User(%s)", user)
            scope.user = user

        if extra is not None:
            for key, value in extra.items():
                log.debug("Sentry: Extra(%s=%s)", key, value)
                scope.set_extra(key, value)

        yield


@contextlib.contextmanager
def enrich_http_error():
    """Enhance Sentry reports for HTTPErrors with additional context about the request and response."""

    with push_scope(propagate=True) as scope:
        try:
            yield
        except requests.exceptions.HTTPError as err:
            # Enhance scope with request and response information
            request: Optional[requests.PreparedRequest] = err.request
            if request:
                scope.set_context(
                    "request",
                    {
                        "url": request.url,
                        "headers": dict(request.headers),
                        "body": _parse_body(request.body, request.headers.get("Content-Type")),
                    },
                )

            response: requests.Response = err.response
            scope.set_context(
                "response",
                {
                    "url": response.url,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": _parse_body(response.text, response.headers.get("Content-Type")),
                },
            )

            raise  # pass err back into `push_scope` for handling


def _parse_body(content: str, content_type: str) -> Union[dict, str]:
    if "application/json" in content_type:
        return json.loads(content)
    if "application/x-www-form-urlencoded" in content_type:
        return urllib.parse.parse_qs(content)
    return content


@contextlib.contextmanager
def push_scope(name=None, *, propagate=True, ignore=(), **tags):
    with sentry_sdk.push_scope() as scope:
        scope.transaction = name
        for k, v in tags.items():
            scope.set_tag(k, v)

        try:
            yield scope
        except BaseException as err:
            # Don't capture ignored exception classes
            if isinstance(err, ignore):
                raise

            # If this is the first time seeing the error, capture it to Sentry with full scope context.
            if not getattr(err, "__sentry__", None):
                log.debug(f"Reporting to Sentry: {err.__class__.__name__}({err})")
                event_id = sentry_sdk.capture_exception(err, scope=scope)
                err.__sentry__ = True
                if event_id:
                    log.info(f"Sentry event id: {event_id}")

            # If this scope is configured to propagate errors, re-raise
            if propagate:
                raise

            # Log the error locally when finished propogating. This should not be re-recorded by Sentry.
            log.error(err, exc_info=True)

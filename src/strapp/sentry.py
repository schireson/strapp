import logging
import contextlib
from typing import Dict, Any, Optional

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

log = logging.getLogger(__name__)


def setup_sentry(dsn, environment=None, service_name=None, level='WARNING', breadcrumb_level='INFO'):
    """Setup sentry.

    It's expected that this function is called once at app startup
    """
    sentry_sdk.init(
        dsn=dsn,
        integrations=[
            LoggingIntegration(level=level, event_level=event_level),
            SqlalchemyIntegration(),
        ],
        attach_stacktrace=True,
        environment=environment,
        server_name=service_name,
    )


@contextlib.contextmanager
def add_context(*, user: Optional[Dict] = None, extra: Optional[Dict[str, Any]] = None, **tags):
    """Add extra context into any captured sentry events.

    Args:
        user: Sets the context's user.
        extra: Add extra non-indexed key/value pairs to the event.
        **tags: Add indexed key/value pairs to the event.

    Tags show up in sentry as tags/pills at the top of the issue to provide context. Furthermore
    They're indexed, and are therefore searchable.
    >>> with add_context(domain_model_id=4, report_type='foo'):
    ...     # Captured sentry events, such as unhandled exceptions will have these attributes
    ...     1 / 0

    Sentry has an explicit notion of a "user", which is handled separately from other context.
    >>> with add_context(user={id: 1}):
    ...     1 / 0

    Extras show up in sentry as extra, non-critical data towards the botton of the issue. They
    just provide additional context, and are not indexed.
    >>> with add_context(extra={'json': 1}):
    ...     1 / 0
    """
    with sentry_sdk.push_scope() as scope:
        for name, value in tags.items():
            scope.set_tag(name, value)

        if user is not None:
            scope.user = user

        if extra is not None:
            for key, value in extra.items():
                scope.set_extra(key, value)

        yield

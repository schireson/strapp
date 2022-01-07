import logging
from typing import Dict, Mapping, Optional

import sqlalchemy.orm

log = logging.getLogger(__name__)


def create_session_cls(config: Mapping, *, scopefunc=None, engine_kwargs: Optional[Dict] = None):
    url_cls = sqlalchemy.engine.url.URL
    if hasattr(url_cls, "create"):
        url_cls = url_cls.create  # type: ignore

    url = url_cls(**dict(config))
    engine = sqlalchemy.create_engine(url, **(engine_kwargs or {}))

    return sqlalchemy.orm.scoping.scoped_session(
        sqlalchemy.orm.session.sessionmaker(bind=engine), scopefunc=scopefunc,
    )


def create_session(
    config: Mapping,
    *,
    scopefunc=None,
    dry_run: bool = False,
    verbosity: int = 0,
    engine_kwargs: Optional[Dict] = None
):
    """Create a sqlalchemy session.

    Args:
        config: The dict-like set of options to :class:`sqlalchemy.engine.url.URL`
        scopefunc: The optional `scopefunc` arg to :class:`sqlalchemy.orm.scoping.scoped_session`
        dry_run: If :code:`True`, wraps the session such that it cannot perform `commit` operations
        verbosity: Only applies to `dry_run` sessions, but when > 0 will log the state of the
            session on would-be commit operations
        engine_kwargs: Optional kwargs to pass through to the :func:`sqlalchemy.create_engine` call
    """
    Session = create_session_cls(config, scopefunc=scopefunc, engine_kwargs=engine_kwargs)
    session = Session()

    if dry_run:
        session = DryRunSession(session, verbosity=verbosity)

    return session


def log_session_state(session):
    for attr in ("new", "dirty", "deleted"):
        session_attr = getattr(session, attr)

        if session_attr:
            log.info("%s data:", attr.title())

            for row in session_attr:
                log.info("%s: %s", attr.upper(), row)


class DryRunSession:
    def __init__(self, session, verbosity=0, log_at_verbosity=1):
        self.session = session
        self.verbosity = verbosity
        self.log_at_verbosity = log_at_verbosity

    def commit(self):
        if self.verbosity >= self.log_at_verbosity:
            log_session_state(self.session)

        self.session.flush()

    def __del__(self):
        self.session.rollback()

    def __getattr__(self, attr):
        return getattr(self.session, attr)

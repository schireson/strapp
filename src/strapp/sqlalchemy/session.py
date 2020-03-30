import sqlalchemy.orm
import logging

log = logging.getLogger(__name__)


def create_session_cls(config: dict, *, scopefunc=None):
    url = sqlalchemy.engine.url.URL(**config)
    engine = sqlalchemy.create_engine(url)
    return sqlalchemy.orm.scoping.scoped_session(
        sqlalchemy.orm.session.sessionmaker(bind=engine), scopefunc=scopefunc,
    )


def create_session(config: dict, *, scopefunc=None, dry_run: bool = False, verbosity: int = 0):
    Session = create_session_cls(config, scopefunc=scopefunc)
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

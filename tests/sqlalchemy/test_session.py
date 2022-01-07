import sqlalchemy
from sqlalchemy.orm.session import Session

from strapp.sqlalchemy.model_base import declarative_base
from strapp.sqlalchemy.session import create_session, DryRunSession, log_session_state


def test_create_session():
    session = create_session({"drivername": "sqlite"})
    assert isinstance(session, Session)


def test_create_session_dry_run():
    session = create_session({"drivername": "sqlite"}, dry_run=True)
    assert isinstance(session, DryRunSession)


Base = declarative_base()


class Foo(Base):
    __tablename__ = "foo"
    id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True)


def test_log_session_state_new(caplog):
    caplog.set_level("DEBUG")

    session = create_session({"drivername": "sqlite"})
    Base.metadata.create_all(bind=session.connection())

    foo_new = Foo(id=1)
    session.add(foo_new)

    log_session_state(session)

    assert len(caplog.records) == 2
    assert caplog.records[0].message == "New data:"
    assert caplog.records[1].message == "NEW: Foo(id=1)"


def test_log_session_state_dirty(caplog):
    caplog.set_level("DEBUG")

    session = create_session({"drivername": "sqlite"})
    Base.metadata.create_all(bind=session.connection())

    foo_dirty = Foo(id=1)
    session.add(foo_dirty)
    session.flush()
    foo_dirty.id = 9

    log_session_state(session)

    assert len(caplog.records) == 2
    assert caplog.records[0].message == "Dirty data:"
    assert caplog.records[1].message == "DIRTY: Foo(id=9)"


def test_log_session_state_deleted(caplog):
    caplog.set_level("DEBUG")

    session = create_session({"drivername": "sqlite"})
    Base.metadata.create_all(bind=session.connection())

    foo_deleted = Foo(id=1)
    session.add(foo_deleted)
    session.flush()
    session.delete(foo_deleted)

    log_session_state(session)

    assert len(caplog.records) == 2
    assert caplog.records[0].message == "Deleted data:"
    assert caplog.records[1].message == "DELETED: Foo(id=1)"


def test_engine_kwargs(caplog):
    caplog.set_level("DEBUG")

    session = create_session(
        {"drivername": "sqlite"}, dry_run=True, verbosity=3, engine_kwargs={"pool_pre_ping": True}
    )
    Base.metadata.create_all(bind=session.connection())

    foo_new = Foo(id=1)
    session.add(foo_new)

    session.commit()
    assert len(caplog.records) == 2


def test_DryRunSession_commit(caplog):
    caplog.set_level("DEBUG")

    session = create_session({"drivername": "sqlite"}, dry_run=True)
    Base.metadata.create_all(bind=session.connection())

    foo_new = Foo(id=1)
    session.add(foo_new)

    session.commit()
    assert len(caplog.records) == 0


def test_DryRunSession_commit_logs(caplog):
    caplog.set_level("DEBUG")

    session = create_session({"drivername": "sqlite"}, dry_run=True, verbosity=3)
    Base.metadata.create_all(bind=session.connection())

    foo_new = Foo(id=1)
    session.add(foo_new)

    session.commit()
    assert len(caplog.records) == 2

from datetime import datetime, timedelta, timezone

import sqlalchemy
import sqlalchemy.ext

from strapp.sqlalchemy.model_base import declarative_base

try:
    from sqlalchemy.orm import declarative_base as sqlalchemy_declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base as sqlalchemy_declarative_base


class Test_declarative_base:
    def test_self_declarative_base(self):
        base = sqlalchemy_declarative_base()
        Base = declarative_base(base, repr=False)

        class Foo(Base):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1)
        assert "Foo object at" in repr(a)

    def test_repr_false(self):
        Base = declarative_base(repr=False)

        class Foo(Base):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1)
        assert "Foo object at" in repr(a)

    def test_repr(self):
        Base = declarative_base(repr=True)

        class Foo(Base):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1)
        assert repr(a) == "Foo(id=1)"

    def test_created_at(self):
        Base = declarative_base()

        class Foo(Base, created_at=True):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1)
        assert repr(a) == "Foo(id=1, created_at=None)"

    def test_updated_at(self):
        Base = declarative_base()

        class Foo(Base, updated_at=True):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1)
        assert repr(a) == "Foo(id=1, updated_at=None)"

    def test_relationship_not_loaded(self, db):
        Base = declarative_base()

        class Foo(Base, updated_at=True):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        class Bar(Base, updated_at=True):
            __tablename__ = "bar"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)
            foo_id = sqlalchemy.orm.deferred(
                sqlalchemy.Column(
                    sqlalchemy.types.Integer(), sqlalchemy.ForeignKey("foo.id"), nullable=False
                )
            )

            foo = sqlalchemy.orm.relationship("Foo")

        Base.metadata.create_all(bind=db.connection())
        foo = Foo(id=1)
        bar = Bar(id=1, foo_id=1)

        db.add(foo)
        db.add(bar)
        db.flush()

        assert repr(bar) == "Bar(foo_id=<not loaded>, id=1, updated_at=None)"

    def test_created_at_set(self, db):
        Base = declarative_base()

        class Foo(Base, created_at=True):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        Base.metadata.create_all(bind=db.connection())
        foo = Foo(id=1)
        db.add(foo)
        db.commit()
        assert foo.created_at is not None

    def test_updated_at_set(self, db):
        Base = declarative_base()

        class Foo(Base, updated_at=True):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        Base.metadata.create_all(bind=db.connection())
        foo = Foo(id=1)
        db.add(foo)
        db.commit()

        foo.id = 2
        db.add(foo)
        db.commit()
        assert foo.updated_at is not None

    def test_deleted_at_set(self, db):
        Base = declarative_base()

        class Foo(Base, deleted_at=True):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False)

        Base.metadata.create_all(bind=db.connection())
        foo = Foo(id=1)
        db.add(foo)
        db.commit()
        assert foo.deleted_at is None

        now = datetime(2020, 1, 1, tzinfo=timezone(timedelta()))
        foo.deleted_at = now
        db.add(foo)
        db.commit()

        db_foo = db.query(Foo).one()
        assert db_foo.deleted_at == now

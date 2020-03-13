from strapp.sqlalchemy.model_base import declarative_base
import sqlalchemy
import sqlalchemy.ext


class Test_declarative_base:
    def test_self_declarative_base(self):
        base = sqlalchemy.ext.declarative.declarative_base()
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

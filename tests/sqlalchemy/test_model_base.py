from strapp.sqlalchemy.model_base import declarative_base
import sqlalchemy


class Test_declarative_base:
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

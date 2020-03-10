import sqlalchemy
import pytest

from strapp.sqlalchemy.model_base import declarative_base
from strapp.sqlalchemy.testing import assert_equals, assert_equals_factory


class Test_assert_equals:
    def test_equals_false(self):
        Base = declarative_base()

        class Foo(Base):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1)
        b = Foo(id=2)
        with pytest.raises(AssertionError):
            assert_equals(a, b)

    def test_equals_tuple(self):
        Base = declarative_base()

        class Foo(Base):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1)
        assert_equals(a, (1,))

    def test_assert_equals(self):
        Base = declarative_base()

        class Foo(Base):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1)
        b = Foo(id=1)
        assert_equals(a, b)

    def test_assert_equals_include(self):
        Base = declarative_base()

        class Foo(Base):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)
            id2 = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1, id2=2)
        b = Foo(id=1, id2=1)
        assert_equals(a, b, include=["id"])
        with pytest.raises(AssertionError):
            assert_equals(a, b, include=["id2"])

    def test_assert_equals_exclude(self):
        Base = declarative_base()

        class Foo(Base):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)
            id2 = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1, id2=2)
        b = Foo(id=1, id2=1)
        assert_equals(a, b, exclude=["id2"])
        with pytest.raises(AssertionError):
            assert_equals(a, b, exclude=["id"])

    def test_assert_equals_factory(self):
        Base = declarative_base()

        class Foo(Base):
            __tablename__ = "foo"
            id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)
            id2 = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True, nullable=False,)

        a = Foo(id=1, id2=2)
        b = Foo(id=1, id2=1)

        assert_models_equal1 = assert_equals_factory(include=["id"])
        assert_models_equal2 = assert_equals_factory(exclude=["id2"])

        assert_models_equal3 = assert_equals_factory(exclude=["id"])
        assert_models_equal4 = assert_equals_factory(include=["id2"])

        assert_models_equal1(a, b)
        assert_models_equal2(a, b)
        with pytest.raises(AssertionError):
            assert_models_equal3(a, b)
            assert_models_equal4(a, b)

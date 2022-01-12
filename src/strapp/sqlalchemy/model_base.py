import operator
from datetime import datetime
from typing import Optional, Type

import sqlalchemy

try:
    from sqlalchemy.orm import DeclarativeMeta as SQLAlchemyDeclarativeMeta  # type: ignore
    from sqlalchemy.orm import declarative_base as sqlalchemy_declarative_base  # type: ignore
except ImportError:
    from sqlalchemy.ext.declarative import DeclarativeMeta as SQLAlchemyDeclarativeMeta
    from sqlalchemy.ext.declarative import declarative_base as sqlalchemy_declarative_base


def repr_fn(instance):
    """Define a generic repr function for sqlalchemy models.

    Args:
        instance: The to generate the `repr` of.
    """
    cls = instance.__class__
    class_name = cls.__name__
    state = sqlalchemy.inspect(cls)

    repr_attrs_list = []
    for attr in state.columns.keys():
        value = "<not loaded>"
        if not state.attrs[attr].deferred:
            value = repr(getattr(instance, attr))
        repr_attrs_list.append(f"{attr}={value}")

    repr_attrs = ", ".join(repr_attrs_list)
    return f"{class_name}({repr_attrs})"


class DeclarativeMeta(SQLAlchemyDeclarativeMeta):
    """Wrap sqlalchemy declarative meta to allow for extra kwargs.
    """

    def __init__(cls, classname, bases, dict_, created_at=False, updated_at=False, **kwargs):
        # SQLAlchemy 1.4.0 and later only work with the metaclass init strategy,
        # requiring use of `setitem`.
        _set_attrs(dict_, created_at=created_at, updated_at=updated_at, op=operator.setitem)
        super().__init__(classname, bases, dict_)

    @classmethod
    def __init_subclass__(cls, created_at=False, updated_at=False, **kwargs):
        super().__init_subclass__(**kwargs)


def declarative_base(
    base: Optional[Type[SQLAlchemyDeclarativeMeta]] = None, *, repr=True, metadata=None
) -> Type[DeclarativeMeta]:
    """Define a declarative base class.

    Args:
        base: Optional alternative base, one will be created if omitted.
        repr: If True, automatically define a `__repr__` method.
        metadata: Passthrough argument to the `declarative_base` function.

    Additionally, subclasses of the resultant `Base` accept the following class
    definition options:

        * created_at: True/False
        * updated_at: True/False

    Examples:
        >>> Base = declarative_base()
        >>> class Example(Base, created_at=True, updated_at=False):
        ...     __tablename__ = 'example'
        ...     id = sqlalchemy.Column(sqlalchemy.types.Integer(), primary_key=True)
    """
    if base is None:
        base: Type[SQLAlchemyDeclarativeMeta] = sqlalchemy_declarative_base(metaclass=DeclarativeMeta, metadata=metadata)  # type: ignore

    class Base(base):  # type: ignore
        __abstract__ = True

        if repr:
            __repr__ = repr_fn

        @classmethod
        def __init_subclass__(cls, created_at=False, updated_at=False, **kwargs):
            super().__init_subclass__(**kwargs)

            # SQLAlchemy before 1.4.0 only work with the init_subclass strategy,
            # requiring use of `setattr`.
            _set_attrs(cls, created_at=created_at, updated_at=updated_at, op=setattr)

    return Base


def _set_attrs(dict_, created_at=False, updated_at=False, op=setattr):
    """Assign created_at/updated_at to the database model.

    Different versions of SQLAlchemy require different strategies of setting
    these values in order for it to work correctly!
    """
    if created_at:
        op(
            dict_,
            "created_at",
            sqlalchemy.Column(
                sqlalchemy.types.DateTime(timezone=True),
                default=datetime.utcnow,
                server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
        )

    if updated_at:
        op(
            dict_,
            "updated_at",
            sqlalchemy.Column(
                sqlalchemy.types.DateTime(timezone=True), onupdate=datetime.utcnow, nullable=True,
            ),
        )

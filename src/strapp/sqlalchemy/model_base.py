from datetime import datetime
from typing import Optional

import sqlalchemy
from sqlalchemy.ext import declarative


def declarative_base(base: Optional[declarative.DeclarativeMeta] = None, *, repr=True):
    """Define a declarative base class.

    Args:
        base: Optional alternative base, one will be created if omitted.
        repr: If True, automatically define a `__repr__` method.

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
        base = declarative.declarative_base(metaclass=_DeclarativeMeta)

    class Base(base):
        __abstract__ = True

        if repr:
            __repr__ = repr_fn

        def __init_subclass__(cls, created_at=False, updated_at=False, **kwargs):
            super().__init_subclass__(**kwargs)

            if created_at:
                cls.created_at = sqlalchemy.Column(
                    sqlalchemy.types.DateTime(timezone=True),
                    default=datetime.utcnow,
                    server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
                    nullable=False,
                )

            if updated_at:
                cls.updated_at = sqlalchemy.Column(
                    sqlalchemy.types.DateTime(timezone=True),
                    onupdate=datetime.utcnow,
                    nullable=True,
                    **kwargs,
                )

    return Base


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


class _DeclarativeMeta(declarative.DeclarativeMeta):
    """Wrap sqlalchemy declarative meta to allow for extra kwargs.
    """

    def __init__(cls, classname, bases, dict_, **kwargs):
        super().__init__(classname, bases, dict_)

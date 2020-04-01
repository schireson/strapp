import functools
from collections import namedtuple

import sqlalchemy


def assert_equals(instance, other, include=None, exclude=None):
    """Produce a generic eq function for sqlalchemy models.

    Args:
        instance: The first instance of a model
        other: The first instance of a model, or other comparable object
        include: The set of columns to include
        exclude: The set of columns to exclude
    """
    instance_eq = _collect_loaded_values(instance, include=include, exclude=exclude)

    other_eq = other
    if isinstance(other, type(instance)):
        other_eq = _collect_loaded_values(other, include=include, exclude=exclude)
    assert instance_eq == other_eq  # nosec


def assert_equals_factory(include=None, exclude=None):
    @functools.wraps(assert_equals)
    def _assert_equals(instance, other):
        return assert_equals(instance, other, include=include, exclude=exclude)

    return _assert_equals


def _collect_loaded_values(instance, include=None, exclude=None):
    """Collect a sqlalchemy model into a comparable object.
    """
    cls = instance.__class__
    class_name = cls.__name__
    state = sqlalchemy.inspect(cls)

    columns = _collect_columns(state.columns.keys(), include=include, exclude=exclude)
    result_cls = namedtuple(class_name, columns)

    result = []
    for column in columns:
        if state.attrs[column].deferred:
            result.append(None)
        else:
            value = getattr(instance, column)
            result.append(value)

    return result_cls(*result)


def _collect_columns(columns, include=None, exclude=None):
    columns = set(columns)

    if include:
        include = set(include)
        if include - columns:
            raise ValueError("Invalid columns given: {}".format(", ".join(include - columns)))

        columns = include

    if exclude:
        exclude = set(exclude)
        if exclude - columns:
            raise ValueError("Invalid columns given: {}".format(", ".join(exclude - columns)))

        columns = columns - exclude

    return sorted(list(columns))

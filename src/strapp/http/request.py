import abc
import contextlib
import socket
from dataclasses import dataclass, replace
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar, Union

import backoff

try:
    from typing import ParamSpec  # type: ignore
except ImportError:
    from typing_extensions import ParamSpec


def from_field(mapper, *fields):
    """Extract a `field` from a given item.

    If more than one `field` is given, select fields recursively.

    Examples:
        >>> def noop(data):
        ...     return data

        >>> mapper = from_field(noop, 'foo')
        >>> data = {'foo': 4}
        >>> mapper(data)
        4

        >>> mapper = from_field(noop, 'foo', 'bar')
        >>> data = {'foo': {'bar': 4}}
        >>> mapper(data)
        4
    """

    def decorator(response):
        context = response
        for field in fields:
            context = context.get(field)
        return mapper(context)

    return decorator


def map_many(mapper):
    """Apply the `mapper` to each item in a series of results rather than the result as a whole.

    Examples:
        >>> def noop(data):
        ...     return data + 1

        >>> mapper = map_many(noop)
        >>> mapper([4, 6, 1, 0])
        [5, 7, 2, 1]
    """

    def decorator(response):
        result = []

        # Return immediately in the case where the response is not iterable.
        if not response:
            return result

        for item in response:
            mapped = mapper(item)
            result.append(mapped)
        return result

    return decorator


def map_first(mapper):
    """Map the first item in a series of results.

    Examples:
        >>> def noop(data):
        ...     return data + 1

        >>> mapper = map_first(noop)
        >>> mapper([4, 6, 1, 0])
        5
    """

    def decorator(response):
        if response:
            return mapper(response[0])
        return None

    return decorator


def into_map(mapper, field):
    """Execute a given mapper for each item in a list, then map the result by some attribute.

    Examples:
        >>> @dataclass
        ... class Foo:
        ...     id: int
        >>> mapper = into_map(Foo, 'id')
        >>> mapper([4, 6, 1, 0])
        {4: Foo(id=4), 6: Foo(id=6), 1: Foo(id=1), 0: Foo(id=0)}
    """

    def decorator(response):
        result = {}

        # Return immediately in the case where the response is not iterable.
        if not response:
            return result

        for item in response:
            mapped = mapper(item)
            key = getattr(mapped, field)
            result[key] = mapped
        return result

    return decorator


def filter_for(mapper, filter_fn):
    """Filter records out during the mapping phase.

    Examples:
        >>> @dataclass
        ... class Foo:
        ...     id: int
        >>> items = [Foo(id=1), Foo(id=2), Foo(id=3)]

        Normally the mapper would be the thing that turns raw json into the above `items`
        >>> noop = lambda x: x

        >>> mapper = filter_for(noop, lambda r: r.id <= 2)
        >>> mapper(items)
        [Foo(id=1), Foo(id=2)]
    """

    def decorator(response):
        return list(filter(filter_fn, mapper(response)))

    return decorator


def flatten(mapper):
    """Flatten the result of a mapper that returns iterables of results.

    Examples:
        >>> def nested(data):
        ...     return [data]

        >>> mapper = flatten(nested)
        >>> data = [{'data': 1}]
        >>> list(mapper(data))
        [{'data': 1}]
    """

    def decorator(response):
        result = []
        for items in mapper(response):
            result.extend(items)
        return result

    return decorator


T = TypeVar("T")


def noop_mapper(response: T) -> T:
    return response


@dataclass
class Request(Generic[T], metaclass=abc.ABCMeta):
    def prepare(self) -> "PreparedRequest[T]":
        """Return a prepared request."""


@dataclass
class PreparedRequest(Request[T]):
    """The static definition of what it takes to make a request."""

    url: str

    method: str = "GET"
    json: Optional[dict] = None
    data: Optional[Union[bytes, Dict, List[Tuple[Any, Any]]]] = None
    files: Optional[dict] = None
    params: Optional[dict] = None
    headers: Optional[dict] = None
    response_mapper: Callable[..., T] = noop_mapper
    map_with_request: bool = False
    is_paginated: bool = True
    extra: Optional[dict] = None

    # A timeout of `None` is meant to indicate the lack of a supplied timeout, i.e. default.
    # A timeout of `0` is meant to indicate an explicit lack of a timeout i.e. infinite.
    timeout: Optional[int] = None

    def prepare(self) -> "PreparedRequest[T]":
        """Produce an identical `PreparedRequest` from the existing one.

        In particular, this can be useful to instantiate a specific request directly
        into a function which accepts a `Request`.
        """
        return replace(self)


P = ParamSpec("P")
R = TypeVar("R")


@contextlib.contextmanager
def managed_request(retries=6, max_time=60 * 5, base=2, factor=3, exceptions=()):
    """Intercept all outgoing requests so they can be safety-wrapped.

    * Increases the default socket timeout for the duration of the request
    * Attempts to retry upon service-degredation level communication failures.
    """
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(max_time)

    def server_unavailable(resp):
        status_code = getattr(resp, "status_code", None)
        return status_code is not None and status_code == 503

    @backoff.on_exception(
        backoff.expo,
        (socket.timeout, BrokenPipeError, ConnectionResetError, *exceptions),
        max_tries=retries,
        max_time=max_time,
        base=base,
        factor=factor,
    )
    @backoff.on_predicate(
        backoff.expo,
        server_unavailable,
        max_tries=retries,
        max_time=max_time,
        base=base,
        factor=factor,
    )
    def request_fn(fn: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        return fn(*args, **kwargs)

    try:
        yield request_fn
    finally:
        socket.setdefaulttimeout(old_timeout)

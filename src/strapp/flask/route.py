from dataclasses import dataclass
from typing import Callable, List


def try_parse(fn, route):
    try:
        return fn(route)
    except (TypeError, ValueError):
        return None


def parse_instance(route):
    if isinstance(route, Route):
        return route


def parse(route):
    method, path, view = route
    return Route.to(method, path, view)


def parse_with_kwargs(route):
    method, path, view, kwargs = route
    return Route.to(method, path, view, **kwargs)


def parse_dict(route):
    return Route.to(**route)


@dataclass
class Route:
    """A representation of a flask route.
    """

    methods: List[str]
    path: str
    view: Callable
    endpoint_: str
    kwargs: dict

    @classmethod
    def to(cls, method, path, view, endpoint=None, **kwargs):
        """Route a method+path to a view function.
        """
        return cls([method], path, view, endpoint_=endpoint, kwargs=kwargs)

    @classmethod
    def parse(cls, route):
        for method in [parse_instance, parse_dict, parse, parse_with_kwargs]:
            result = try_parse(method, route)
            if result:
                return result
        raise ValueError(f"Could not parse {route} as route")

    @property
    def endpoint(self):
        if self.endpoint_:
            return self.endpoint_
        return ".".join(
            [self.path.replace("/", "."), "-".join([m.lower() for m in self.methods])]
        )  # ".".join([self.view.__module__, self.view.__name__])

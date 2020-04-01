import pytest

from strapp.flask import Route


def view():
    pass


def test_parse_instance():
    expected_result = Route.to("GET", "/foo", view)
    result = Route.parse(expected_result)
    assert expected_result == result


def test_parse():
    in_route = ("GET", "/foo", view)
    result = Route.parse(in_route)

    expected_result = Route.to("GET", "/foo", view)
    assert expected_result == result


def test_parse_with_kwargs():
    in_route = ("GET", "/foo", view, dict(endpoint="woah"))
    result = Route.parse(in_route)

    expected_result = Route.to("GET", "/foo", view, endpoint="woah")
    assert expected_result == result


def test_parse_dict():
    in_route = dict(method="GET", path="/foo", view=view)
    result = Route.parse(in_route)

    expected_result = Route.to("GET", "/foo", view)
    assert expected_result == result


def test_invalid_parse():
    in_route = (1, 2, 3, 4, 5, 6)
    with pytest.raises(ValueError) as e:
        Route.parse(in_route)
    assert str(e.value) == "Could not parse (1, 2, 3, 4, 5, 6) as route"

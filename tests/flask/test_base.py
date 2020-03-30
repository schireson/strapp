import flask
from unittest.mock import patch

from strapp.flask import BadRequest, create_app, default_error_handlers, Route


def test_error_handlers_werkzeug():
    app = create_app([], error_handlers=default_error_handlers)
    with app.test_client() as client:
        response = client.get("/foo")

    assert response.json == {
        "error": (
            "(NotFound) 404 Not Found: The requested URL was not found on the server. "
            "If you entered the URL manually please check your spelling and try again."
        )
    }
    assert response.status_code == 404


def test_error_handlers_normal_exception():
    def err():
        raise Exception("agh!")

    app = create_app(routes=[Route.to("GET", "/foo", err)], error_handlers=default_error_handlers)
    with app.test_client() as client:
        response = client.get("/foo")

    assert response.json["error"] == "(Exception) agh!"
    assert response.status_code == 500
    assert "traceback" in response.json


@patch("strapp.flask.error.sentry_sdk", new=None)
def test_error_handlers_normal_exception_no_sentry():
    def err():
        raise Exception("agh!")

    app = create_app(routes=[Route.to("GET", "/foo", err)], error_handlers=default_error_handlers)
    with app.test_client() as client:
        response = client.get("/foo")

    assert response.json["error"] == "(Exception) agh!"
    assert response.status_code == 500
    assert "traceback" in response.json


def test_error_handlers_handled_exception():
    def err():
        raise BadRequest("agh!")

    app = create_app(routes=[Route.to("GET", "/foo", err)], error_handlers=default_error_handlers)
    with app.test_client() as client:
        response = client.get("/foo")

    assert response.json == {"error": "agh!"}
    assert response.status_code == 400


def test_route_registered():
    def view():
        return flask.jsonify(5)

    app = create_app(routes=[Route.to("GET", "/foo", view)])
    with app.test_client() as client:
        response = client.get("/foo")

    assert response.json == 5
    assert response.status_code == 200


def test_non_proxied():
    create_app([], proxied=False)

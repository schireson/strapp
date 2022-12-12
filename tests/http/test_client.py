from unittest.mock import patch

import pytest

from strapp.http.client import Http4XXError, Http5XXError, HttpClient


def test_4xx(responses):
    responses.add(responses.GET, "http://foo/whatup", json={"error": "not found"}, status=404)

    client = HttpClient("http://foo")
    with pytest.raises(Http4XXError):
        client.make_request("GET", "whatup")
    assert len(responses.calls) == 1


def test_5xx(responses):
    responses.add(
        responses.GET,
        "http://foo/whatup",
        json={"error": "internal server error"},
        status=500,
    )

    client = HttpClient("http://foo")
    with pytest.raises(Http5XXError):
        client.make_request(
            "GET", "whatup", json={"key": "value"}, retries=4, backoff_base=0, backoff_factor=0
        )
    assert len(responses.calls) == 4


def test_log_response_body_json(responses):
    responses.add(
        responses.GET,
        "http://foo/whatup",
        json={"all": "good"},
        status=200,
    )

    client = HttpClient("http://foo")

    with patch("strapp.http.client.log.debug") as p:
        client.make_request("GET", "whatup", log_response_body=True)

    assert "{'all': 'good'}" in str(p.call_args[0])


def test_log_response_body_text(responses):
    responses.add(
        responses.GET,
        "http://foo/whatup",
        body="<SOMERANDOHTML/>",
        status=200,
    )
    client = HttpClient("http://foo")

    with patch("strapp.http.client.log.debug") as p:
        client.make_request("GET", "whatup", log_response_body=True)

    assert "<SOMERANDOHTML/>" in str(p.call_args[0])

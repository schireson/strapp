from dataclasses import dataclass
from typing import Any, Callable, Dict
from unittest.mock import Mock

import requests

from strapp.http.request import (
    filter_for,
    flatten,
    from_field,
    into_map,
    managed_request,
    map_many,
    noop_mapper,
    PreparedRequest,
    Request,
    T,
)
from tests import FakeHttpClient


@dataclass
class Foo:
    name: str
    age: int

    @classmethod
    def from_response(cls, response: Dict[str, Any]) -> "Foo":
        return cls(**response)


@dataclass
class FakeRequest(Request):
    response_mapper: Callable = noop_mapper

    def prepare(self) -> "PreparedRequest":
        return PreparedRequest(
            method="GET", url="some_endpoint", response_mapper=self.response_mapper
        )


class Test_managed_request:
    def test_exceptions_arg(self):
        fn = Mock(
            side_effect=[
                requests.exceptions.ConnectionError(),
                requests.exceptions.ConnectionError(),
                "woah",
            ]
        )
        with managed_request(exceptions=(requests.exceptions.ConnectionError,)) as request:
            result = request(fn)

        assert result == "woah"
        assert fn.call_count == 3


class Test_Request:
    base_url = "http://example.com"

    def test_request_noop_mapper(self, responses):
        responses.add(responses.GET, f"{self.base_url}/some_endpoint", json={"hello": "world"})
        client = FakeHttpClient.setup_client(base_url=self.base_url)

        response = client.request(FakeRequest())

        assert response == {"hello": "world"}

    def test_request_filter_for(self, responses):
        responses.add(
            responses.GET,
            f"{self.base_url}/some_endpoint",
            json=[1, 2, 3, 4],
        )
        client = FakeHttpClient.setup_client(base_url=self.base_url)

        response = client.request(
            FakeRequest(response_mapper=filter_for(noop_mapper, lambda r: r <= 2))
        )

        assert response == [1, 2]

    def test_request_from_field(self, responses):
        responses.add(
            responses.GET,
            f"{self.base_url}/some_endpoint",
            json={"data": [1, 2, 3, 4], "status": 200},
        )
        client = FakeHttpClient.setup_client(base_url=self.base_url)

        response = client.request(FakeRequest(response_mapper=from_field(noop_mapper, "data")))

        assert response == [1, 2, 3, 4]

    def test_request_map_many(self, responses):
        responses.add(
            responses.GET,
            f"{self.base_url}/some_endpoint",
            json=[{"name": "foo", "age": 1}, {"name": "bar", "age": 2}],
        )

        client = FakeHttpClient.setup_client(base_url=self.base_url)

        response = client.request(FakeRequest(response_mapper=map_many(Foo.from_response)))

        assert response == [Foo(name="foo", age=1), Foo(name="bar", age=2)]

    def test_request_into_map(self, responses):
        responses.add(
            responses.GET,
            f"{self.base_url}/some_endpoint",
            json=[{"name": "foo", "age": 1}, {"name": "bar", "age": 2}],
        )

        client = FakeHttpClient.setup_client(base_url=self.base_url)

        response = client.request(FakeRequest(response_mapper=into_map(Foo.from_response, "name")))

        assert response == {"foo": Foo(name="foo", age=1), "bar": Foo(name="bar", age=2)}

    def test_request_flatten(self, responses):
        responses.add(
            responses.GET,
            f"{self.base_url}/some_endpoint",
            json=["hello"],
        )

        client = FakeHttpClient.setup_client(base_url=self.base_url)

        response = client.request(FakeRequest(response_mapper=flatten(noop_mapper)))

        assert response == ["h", "e", "l", "l", "o"]


def test_prepared_request_typing(responses) -> None:
    @dataclass
    class Bar:
        id: int

    class Foo(Request[Bar]):
        def prepare(self) -> PreparedRequest[Bar]:
            return PreparedRequest(url="http://wat", response_mapper=Bar)

    class Client:
        def request(self, request: Request[T]) -> T:
            prepared_request = request.prepare()
            response = requests.get(prepared_request.url)
            return prepared_request.response_mapper(response.json())

    responses.add(responses.GET, "http://wat", json=1)

    client = Client()
    request = Foo()
    bar = client.request(request)

    assert bar.id == 1

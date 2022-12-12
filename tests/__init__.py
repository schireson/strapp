from dataclasses import dataclass

from strapp.http.client import HttpClient
from strapp.http.request import managed_request, Request


@dataclass
class FakeHttpClient:
    base_url: str
    client: HttpClient

    @classmethod
    def setup_client(cls, base_url: str) -> "FakeHttpClient":
        return cls(base_url=base_url, client=HttpClient(base_url=base_url))

    def request(self, request: Request):
        prepared_request = request.prepare()

        with managed_request() as make_request:
            request_args = {
                "method": prepared_request.method,
                "url": prepared_request.url,
                "params": prepared_request.params,
                "data": prepared_request.data,
            }

            raw_response = make_request(self.client.make_request, **request_args)
            response = raw_response.json()

            return prepared_request.response_mapper(response)

from json import JSONDecodeError
from pprint import pformat

import backoff
import requests
import urllib3
from setuplog import log


class Http4XXError(requests.exceptions.HTTPError):
    """A request returned a 4XX code."""

    @classmethod
    def from_http_error(cls, http_error):
        new_error = cls(http_error)
        new_error.request = http_error.request
        new_error.response = http_error.response
        return new_error


class Http5XXError(requests.exceptions.HTTPError):
    """A request returned a 5XX code."""

    @classmethod
    def from_http_error(cls, http_error):
        new_error = cls(http_error)
        new_error.request = http_error.request
        new_error.response = http_error.response
        return new_error


def default_give_up_retries(e):
    if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
        return 400 <= e.response.status_code < 500 and e.response.status_code != 429
    elif (
        isinstance(e, requests.exceptions.ConnectionError)
        or isinstance(e, requests.exceptions.Timeout)
        or isinstance(e, urllib3.exceptions.ReadTimeoutError)
    ):
        return False
    else:
        return True


class HttpClient:
    def __init__(self, base_url, authenticator=None):
        self._base_url = base_url
        self._authenticator = authenticator
        self._session = None

    @property
    def session(self):
        if not self._session:
            session = requests.Session()
            self._session = session

            if self._authenticator:
                self._authenticator(self)

        return self._session

    def set_header(self, header, value):
        self.session.headers[header] = value

    def make_request(
        self,
        method,
        url="",
        use_base_url=True,
        log_request_body=True,
        log_response_body=False,
        retries=4,
        backoff_base=2,
        backoff_factor=3,
        error_handler=None,
        headers=None,
        params=None,
        data=None,
        files=None,
        auth=None,
        timeout=20,
        json=None,
    ):
        # If a 4XX error is raised - give up immediately
        # Otherwise retry the request a number of times while backing off
        @backoff.on_exception(
            backoff.expo,
            (
                requests.exceptions.HTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ),
            max_time=210,
            max_tries=retries,
            giveup=default_give_up_retries,
            logger=None,
            base=backoff_base,
            factor=backoff_factor,
        )
        def _request(fq_url):
            response = self.session.request(
                method,
                fq_url,
                headers=headers,
                params=params,
                data=data,
                files=files,
                auth=auth,
                timeout=timeout,
                json=json,
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if error_handler:
                    response = error_handler(e)
                else:
                    raise
            return response

        if use_base_url:
            segments = [self._base_url, url]
            url = "/".join([segment for segment in segments if segment])

        pparams = pformat(params or "")
        log.debug("Request: %s %s %s", method, url, pparams)
        if log_request_body and json:
            log.debug("Request Body:\n%s", pformat(json))

        try:
            response = _request(url)

            if log_response_body:
                try:
                    body = response.json()
                except JSONDecodeError:
                    body = response.text
                else:
                    body = pformat(body)

                log.debug("Response Body:\n%s", body)

            return response

        except requests.exceptions.HTTPError as e:
            log.info(e, exc_info=True)

            if getattr(e, "response", None) is None:
                raise

            log_template = "Failed request %s with code `%d` and body: `%s`"
            log.info(log_template, url, e.response.status_code, e.response.text)

            if e.response.status_code >= 500:
                raise Http5XXError.from_http_error(e)

            if e.response.status_code >= 400:
                raise Http4XXError.from_http_error(e)

            raise

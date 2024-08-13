from unittest import mock

import pytest
import requests

from strapp.sentry import enrich_http_error, push_scope, sentry_sdk

REQUEST_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
REQUEST_BODY = {
    "client_id": ["480bf9-f0291-012301-d1e0cb3fb25f"],
    "client_secret": "blah-secret-blah",
    "grant_type": ["refresh_token"],
}
RESPONSE_BODY = {
    "correlation_id": "758067b6-b909-41be-9871-13963fa29c8b",
    "error": "invalid_grant",
    "error_codes": [70000],
}


@pytest.fixture
def sentry_capture_exception():
    with mock.patch("strapp.sentry.sentry_sdk.capture_exception", autospec=True) as fn:
        yield fn


@pytest.fixture
def sentry_push_scope():
    try:
        sentry_push_scope = sentry_sdk.new_scope
    except AttributeError:
        sentry_push_scope = sentry_sdk.push_scope

    scope_name = sentry_push_scope.__name__

    with mock.patch(f"strapp.sentry.sentry_sdk.{scope_name}", autospec=True) as fn:
        yield fn


class Test_EnrichHttpError:
    def test_it_enriches_sentry_exceptions(
        self, responses, sentry_capture_exception, sentry_push_scope
    ):
        responses.add(responses.POST, REQUEST_URL, json=RESPONSE_BODY, status=400)

        with pytest.raises(requests.HTTPError) as excinfo:
            with enrich_http_error():  # does not catch exceptions
                resp = requests.post(REQUEST_URL, json=REQUEST_BODY)
                resp.raise_for_status()

        # Validate exception captured and recorded
        mock_scope = sentry_push_scope.return_value.__enter__.return_value
        sentry_capture_exception.assert_called_once_with(excinfo.value, scope=mock_scope)

        # Validate scope contexts were set correctly
        assert mock_scope.set_context.call_count == 2

        call_name, call_body = mock_scope.set_context.call_args_list[0][0]
        assert call_name == "request"
        assert call_body["url"] == REQUEST_URL
        assert call_body["body"] == REQUEST_BODY

        call_name, call_body = mock_scope.set_context.call_args_list[1][0]
        assert call_name == "response"
        assert call_body["url"] == REQUEST_URL
        assert call_body["status_code"] == 400
        assert call_body["headers"] == {"Content-Type": "application/json"}
        assert call_body["body"] == RESPONSE_BODY


class Test_PushScope:
    def test_it_configures_scope(self, sentry_capture_exception, sentry_push_scope):
        with push_scope("test_scope", tag="tag") as scope:
            assert scope.transaction == "test_scope"
            scope.set_tag.assert_called_once_with("tag", "tag")

        assert sentry_push_scope.return_value.__enter__.return_value == scope
        assert sentry_push_scope.return_value.__enter__.return_value.set_tag.call_count == 1

        mock_scope = sentry_push_scope.return_value.__enter__.return_value
        mock_scope.set_tag.assert_called_once_with("tag", "tag")

    def test_it_captures_exceptions(self, sentry_capture_exception, sentry_push_scope):
        sample_exception = Exception("sample exception")

        with push_scope(propagate=False):
            raise sample_exception

        mock_scope = sentry_push_scope.return_value.__enter__.return_value
        sentry_capture_exception.assert_called_once_with(sample_exception, scope=mock_scope)

    def test_it_propagates_exceptions(self, sentry_capture_exception):
        sample_exception = Exception("sample exception")

        with pytest.raises(sample_exception.__class__) as excinfo:
            with push_scope(propagate=True):
                raise sample_exception

        assert excinfo.value is sample_exception

    def test_it_nests_correctly(self, sentry_capture_exception):
        sample_exception = Exception("sample exception")

        with push_scope("outer_scope", propagate=False) as outer_scope:
            with push_scope("inner_scope", propagate=True):
                raise sample_exception

            sentry_capture_exception.assert_called_once_with(sample_exception, scope=outer_scope)

from unittest.mock import call, patch

import click
from click.testing import CliRunner

from strapp.click import Resolver
from strapp.click.sentry import capture_usage_errors


def test_capture_usage_errors():
    resolver = Resolver()

    @capture_usage_errors(
        dsn=None,
        environment="environment",
        release="release",
        server_name="server_name",
    )
    @resolver.group()
    def cli():
        ...

    with patch("sentry_sdk.init") as mock_init:
        with patch("sentry_sdk.capture_exception") as mock_capture:
            CliRunner().invoke(cli, ["not-a-command"])

    mock_init.assert_called_once_with(
        dsn=None,
        environment="environment",
        release="release",
        server_name="server_name",
    )

    mock_capture.assert_called_once()
    mock_capture.call_args == call(click.exceptions.UsageError("No such command 'not-foo'."))

import contextlib
from typing import Optional

import click
import sentry_sdk


class ClickProxy:
    def __init__(self, cli, wrapper):
        self.cli = cli
        self.wrapper = wrapper

    def __call__(self, *args, **kwargs):
        with self.wrapper():
            self.cli(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.cli, name)

    def main(self, *args, **kwargs):
        """Support testing via CliRunner.invoke."""
        with self.wrapper():
            self.cli.main(*args, **kwargs)


def capture_usage_errors(
    dsn: Optional[str] = None,
    environment: Optional[str] = None,
    release: Optional[str] = None,
    server_name: Optional[str] = None,
):
    def decorator(cli):
        @contextlib.contextmanager
        def wrapper():
            sentry_sdk.init(
                dsn=dsn,
                environment=environment,
                release=release,
                server_name=server_name,
            )
            try:
                yield
            except SystemExit as ex:  # click throws SystemExits on CLI end-of-task
                context = getattr(ex, "__context__")
                if isinstance(context, click.exceptions.UsageError):
                    sentry_sdk.capture_exception(
                        click.exceptions.UsageError(context.format_message())
                    )
                raise

        return ClickProxy(cli, wrapper)

    return decorator

# flake8: noqa
import click

from strapp.click.resolver import Resolver

option = click.option
argument = click.argument

try:
    import pytest
except ImportError:  # pragma: nocover
    pass
else:
    pytest.register_assert_rewrite("strapp.click.testing")
    del pytest
finally:
    from strapp.click import testing

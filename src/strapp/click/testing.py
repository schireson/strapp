import contextlib
import unittest.mock
from dataclasses import dataclass

from click.testing import CliRunner, Result


@dataclass
class ClickResult:
    """Wrapper around :class:`click.Result`.

    Adds additional convenience methods.
    """

    result: Result

    def assert_successful(self):
        """Assert the command executed successfully and print the command output if the assertion is false.
        """
        if self.result.exit_code != 0:
            if self.result.exception:
                print(self.result.exception)

            print(self.result.output)
        assert self.result.exit_code == 0  # nosec

    def assert_unsuccessful(self):
        """Assert the command executed successfully and print the command output if the assertion is false.
        """
        if self.result.exit_code == 0:
            print(self.result.output)
        assert self.result.exit_code == 1  # nosec

    def __getattr__(self, attr):
        return getattr(self.result, attr)


class ClickRunner:
    """Wrap click's built-in testing facilities.

    Args:
        cli: The base cli being tested/executed.
        echo_stdin: When :code:`True`, writes stdin input to stdout. Defaults to :code:`True`.

    Examples:
        >>> import pytest
        >>> from strapp.click.testing import ClickRunner

        It can be convenient to put the runner in a fixture to deduplicate common patches, or other
        setup.

        >>> @pytest.fixture
        ... def runner():
        ...     # import base_cli from wherever you've defined it
        ...     return ClickRunner(base_cli).patch('projectname.cli.base.Config', new={})

        You can then futher patch from inside the test, and invoke the command normally. An important
        difference with the normal click test runner is that we accept :code:`*args` for the
        cli command's arguments, rather than a list.

        >>> def test_some_command(runner):
        ...     runner.patch('projectname.do_something', return_value=None)
        ...     result = runner.invoke('commandset1', 'subcommand', '--some-option', 'foo')
        ...
        ...     result.assert_successful()
        ...     assert result.output == '...'
    """

    def __init__(self, cli, echo_stdin=True):
        self.cli = cli
        self.runner = CliRunner(echo_stdin=echo_stdin)

        self.patches = []

    def patch(self, path, *args, **kwargs):
        """Describe a patch to be applied upon a call to :meth:`Runner.invoke`.

        Patches are **not** applied at the time of the call, they are applied only during an
        invoked cli command.
        """
        self.patches.append((path, args, kwargs))
        return self

    def invoke(self, *args, **kwargs) -> ClickResult:
        """Invoke a cli command.

        Args:
            *args: The cli command arguments.
            **kwargs: Passed through to the vanilla :class:`click.CliRunner.invoke`.

        Returns:
            A :class:`ClickResult`.
        """
        with contextlib.ExitStack() as stack:
            for path, pargs, pkwargs in self.patches:
                stack.enter_context(unittest.mock.patch(path, *pargs, **pkwargs))

            result = self.runner.invoke(self.cli, args, **kwargs)
        return ClickResult(result)

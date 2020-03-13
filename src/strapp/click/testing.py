import contextlib
import logging
import unittest.mock
from dataclasses import dataclass

from click.testing import CliRunner, Result


log = logging.getLogger(__name__)


class ClickRunner:
    def __init__(self, cli, echo_stdin=True):
        self.cli = cli
        self.runner = CliRunner(echo_stdin=echo_stdin)

        self.patches = []

    def patch(self, path, *args, **kwargs):
        self.patches.append((path, args, kwargs))
        return self

    def invoke(self, *args, **kwargs):
        with contextlib.ExitStack() as stack:
            for path, pargs, pkwargs in self.patches:
                stack.enter_context(unittest.mock.patch(path, *pargs, **pkwargs))

            return ClickResult(self.runner.invoke(self.cli, args, **kwargs))


@dataclass
class ClickResult:
    result: Result

    def assert_successful(self):
        if self.result.exit_code:
            log.warning(self.result.output)
        assert self.result.exit_code == 0

    def assert_unsuccessful(self):
        if self.result.exit_code:
            log.warning(self.result.output)
        assert self.result.exit_code == 1

    def __getattr__(self, attr):
        return getattr(self.result, attr)

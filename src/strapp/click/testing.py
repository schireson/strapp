import contextlib
import functools
import inspect
import traceback
import unittest.mock
from dataclasses import dataclass

import click
from click.testing import CliRunner, Result

import sentry_sdk
from setuplog import log


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

    def __getattr__(self, attr):
        return getattr(self.result, attr)

import click
import pytest
import sentry_sdk

from strapp.click import Resolver
from strapp.click.testing import ClickRunner


def test_resolve():
    def example():
        return 4

    resolver = Resolver(example=example)

    def requires(example):
        return example

    result = resolver.resolve(requires)
    assert result == {"example": 4}

    assert requires(**result) == 4


def test_resolve_value_already_exists():
    def example():
        return 4

    def upstream(example):
        return example

    def upstream2(example):
        return example

    resolver = Resolver(example=example, upstream=upstream, upstream2=upstream2)

    def requires(upstream, upstream2):
        return (upstream, upstream2)

    result = resolver.resolve(requires)
    assert result == {"upstream": 4, "upstream2": 4}

    assert requires(**result) == (4, 4)


def test_group():
    resolver = Resolver()

    @resolver.group()
    def foo():
        pass

    result = ClickRunner(foo).invoke()
    assert result.exit_code == 0


def test_sub_group():
    resolver = Resolver()

    @resolver.group()
    def foo():
        pass

    @resolver.group(foo)
    def sub_foo():
        pass

    result = ClickRunner(foo).invoke("sub-foo")
    result.assert_successful()


def test_command():
    resolver = Resolver()

    @resolver.group()
    def foo():
        pass

    @resolver.command(foo)
    def command():
        pass

    result = ClickRunner(foo).invoke("command")
    result.assert_successful()


def test_handled_error():
    resolver = Resolver()

    @resolver.group()
    def foo():
        pass

    @resolver.command(foo)
    def command():
        raise click.ClickException("woah!")

    result = ClickRunner(foo).invoke("command")
    result.assert_unsuccessful()
    assert "woah!" in result.output


@pytest.mark.parametrize("sentry_sdk", (sentry_sdk, None))
def test_unhandled_error(sentry_sdk):
    resolver = Resolver()

    @resolver.group()
    def foo():
        pass

    @resolver.command(foo)
    def command():
        raise Exception("foo")

    result = (
        ClickRunner(foo).patch("strapp.click.resolver.sentry_sdk", new=sentry_sdk).invoke("command")
    )

    result.assert_unsuccessful()
    assert "Traceback" in result.output
    assert "foo" in result.output


def test_bad_assertion_successful():
    resolver = Resolver()

    @resolver.group()
    def foo():
        pass

    @resolver.command(foo)
    def command():
        raise Exception("foo")

    result = (
        ClickRunner(foo).patch("strapp.click.resolver.sentry_sdk", new=sentry_sdk).invoke("command")
    )

    with pytest.raises(AssertionError):
        result.assert_successful()


def test_bad_assertion_unsuccessful():
    resolver = Resolver()

    @resolver.group()
    def foo():
        pass

    @resolver.command(foo)
    def command():
        pass

    result = (
        ClickRunner(foo).patch("strapp.click.resolver.sentry_sdk", new=sentry_sdk).invoke("command")
    )

    with pytest.raises(AssertionError):
        result.assert_unsuccessful()


def test_value_without_producer():
    resolver = Resolver()
    resolver.register_values(a=4)

    def foo(a):
        return a

    result = resolver.resolve(foo)
    assert result == {"a": 4}


def test_double_submission_group():
    resolver = Resolver()
    resolver.register_values(a=4)

    @resolver.group()
    @click.option("--a")
    def group(a):
        pass

    @resolver.command(group)
    def foo(a):
        pass

    result = ClickRunner(group).invoke("--a", "woah", "foo")

    result.assert_successful()


def test_double_submission_command():
    resolver = Resolver()
    resolver.register_values(a=4)

    @resolver.group()
    def group():
        pass

    @resolver.command(group)
    @click.option("--a")
    def foo(a):
        pass

    result = ClickRunner(group).invoke("foo", "--a", "woah")

    result.assert_successful()

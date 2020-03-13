import functools
import inspect
import traceback

import click

try:
    import sentry_sdk
except ImportError:  # pragma: nocover
    sentry_sdk = None  # type: ignore


class Resolver:
    """Wrapper click command/group decorators to automatically provide contextual objects to cli commands.

    Examples:
        >>> from strapp import click
        >>>
        >>> def config():
        ...     return {"value": 1}
        >>>
        >>> def database_engine():
        ...     return ...
        >>>
        >>> resolver = click.Resolver(
        ...     config=config,
        ...     database_engine=database_engine,
        ... )
        >>>
        >>> @resolver.group()
        ... def cli():
        ...     pass
        >>>
        >>> @resolver.command(cli)
        ... @click.option('--option')
        ... def command(config, database_engine):
        ...     pass

    """

    def __init__(self, **producers):
        self.producers = producers
        self.values = {}

    def register_values(self, **values):
        self.values.update(values)

    def reset_cache(self):
        self.values = {}

    def resolve(self, fn):
        arg_context = {}

        signature = inspect.signature(fn)
        for param_name, param in signature.parameters.items():
            producer = self.producers.get(param_name)
            if param_name not in self.values:
                if not producer:
                    continue

                context = self.resolve(producer)
                self.values[param_name] = producer(**context)

            arg_context[param_name] = self.values[param_name]

        return arg_context

    def group(self, cli=None, *group_args, **group_kwargs):
        if cli is None:
            cli = click

        def decorator(fn):
            @cli.group(*group_args, **group_kwargs)
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                context = self.resolve(fn)
                final_kwargs = {**context, **kwargs}
                result = fn(*args, **final_kwargs)
                return result

            return wrapper

        return decorator

    def command(self, group, *command_args, **command_kwargs):
        def decorator(fn):
            @group.command(*command_args, **command_kwargs)
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                context = self.resolve(fn)
                final_kwargs = {**context, **kwargs}
                try:
                    return fn(*args, **final_kwargs)
                except (click.ClickException, click.Abort):
                    raise
                except Exception as e:
                    click.echo(traceback.format_exc())
                    if sentry_sdk:
                        sentry_sdk.capture_exception(e)
                    raise click.ClickException(str(e))

            return wrapper

        return decorator

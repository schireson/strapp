import functools
import inspect
import traceback

import click

import sentry_sdk


option = click.option
argument = click.argument


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

        for attr, component in self.producers.items():
            if not callable(component):
                self.values[attr] = component

    def register_values(self, **values):
        self.values.update(values)

    def resolve(self, fn):
        arg_context = {}

        signature = inspect.signature(fn)
        for param_name, param in signature.parameters.items():
            producer = self.producers.get(param_name)
            if param_name not in self.values:
                if not producer:
                    continue

                if param_name not in self.values:
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
                result = fn(*args, **kwargs, **context)
                return result

            return wrapper

        return decorator

    def command(self, group, *command_args, **command_kwargs):
        def decorator(fn):
            @group.command(*command_args, **command_kwargs)
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                context = self.resolve(fn)

                try:
                    return fn(*args, **kwargs, **context)
                except click.ClickException:
                    raise
                except Exception as e:
                    click.echo(traceback.format_exc())
                    sentry_sdk.capture_exception(e)
                    raise click.Abort(str(e))

            return wrapper

        return decorator

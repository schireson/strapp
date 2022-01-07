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

    Args:
        producers: A mapping from the name that a resource should resolve to when a command asks for it,
            to a callable which can produce that resource. That callable can accept any other resource
            (so long as there are no cycles which make it impossible to resolve a given resource).

    Examples:
        >>> from strapp import click
        >>>
        >>> def config():
        ...     return {"value": 1}
        >>>
        >>> def database_engine(config):
        ...     return ...
        >>>
        >>> resolver = Resolver(
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
        ... def command(database_engine):
        ...     pass

    """

    def __init__(self, **producers):
        self.producers = producers
        self.values = {}

    def register_values(self, **values):
        """Add i.e. already resolved "values" to the resolver.

        This is typically used for things which are produced from inside a command/group itself.

        Examples:
            >>> resolver = Resolver()
            >>>
            >>> @resolver.group()
            ... @click.option('--dry-run', is_flag=True)
            ... @click.option('--verbose', count=True, default=0)
            ... def cli(dry_run, verbose):
            ...     resolver.register_value(dry_run=dry_run, verbosity=verbose)
        """
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
        """Alias :func:`click.group`, which can automatically resolve and inject arguments.
        """
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
        """Alias :func:`click.command`, which can automatically resolve and inject arguments.

        The primary difference between this and :func:`click.command` is that :meth:`Resolver.command`
        accepts its cli group as an argument, rather than being a method on the group itself.
        """

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

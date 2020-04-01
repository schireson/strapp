Click
=====

The CLI applications we write usually tend to follow the same pattern:

* All commands require logging/sentry to have been initialized
* All commands require being wrapped to handle uncaught exceptions
* All commands require one or more of: config, one or more database connections, or one or more API clients of
  some sort.
* Often we want some way to manage verbosity
* Often we want some way to run idempotent, equivalents of commands, without committing
  any changes they might make.

The mechanism strapp exposes to facilitate these requirements and is the :class:`Resolver`.

The two primary goals were:

* Enable the production of the various objects cli command invocations might require lazily, such
  that any command which did not require i.e. config, did not load config.
* Reduce the boilerplate required to either inject or construct those objects.

Resolver
--------

.. automodule:: strapp.click
    :members: Resolver

Again note: if at any time, the patterns expected by Strapp dont work in a given situation,
resolver methods always return :ref:`click`-native primitives which can used normally, using
normal click patterns.

With that being said, a typical click project using Strapp tends to look like so:

.. code-block::

   pyproject.toml / setup.py
   src/
       projectname/
           cli/
               __init__.py
               base.py
               commandset1.py
               commandset2.py
            ... the rest of the project


We then use the :code:`pyproject.toml`/:code:`setup.py` to produce an entrypoint script.

.. code-block:: toml
   :caption: pyproject.toml

   [tool.poetry.scripts]
   projectname = "projectname.cli:run"


In order to avoid circular imports when making use of the resolver in dependent subcommands, we
imperitively add the commands to the base cli, after everything has been constructed.

.. code-block:: python
   :caption: __init__.py

   # flake8: noqa
   from platform_actions.cli import base, commandset1, commandset2

   base.cli.add_command(commandset1.commandset1)
   base.cli.add_command(commandset2.commandset2)


   def run():
       base.cli()


In :code:`base.py`, we produce callables for all the resolvable resources, and instantiate the resolver.

.. code-block:: python
   :caption: base.py

   import click
   import strapp.click
   import strapp.sqlalchemy
   import projectname
   from configly import Config

   def config():
       return Config.from_yaml("config.yml")

   def api_client(config):
       return projectname.api_client.APIClient(config.api_client)

   def postgres(config, dry_run):
       return strapp.sqlalchemy.create_session(config.postgres, dry_run=dry_run)

   def redshift(config, dry_run):
       return strapp.sqlalchemy.create_session(config.redshift, dry_run=dry_run)

   resolver = strapp.click.Resolver(
       config=config,
       postgres=postgres,
       redshift=redshift,
       api_client=api_client,
   )

   @resolver.group()
   @click.option("--dry-run", is_flag=True)
   @click.option("-v", "--verbose", count=True, default=0)
   def cli(config: Config, dry_run, verbose):
       resolver.register_values(dry_run=dry_run, verbosity=verbose)


Optionally, this :code:`cli` base group is the ideal spot to integrate with :ref:`logging`.

And finally, commandset1/2 can be structured however they please. We tend to follow a pattern like:

.. code-block:: python
   :caption: commandset1.py

   import click
   from projectname.cli.base import resolver
   import projectname

   @resolver.group()
   def commandset1():
       pass

   @resolver.command(commandset1, help='subcommand')
   @click.option('--some-option')
   def subcommand(postgres, redshift, api_client):
       projectname.do_something(postgres, redshift, api_client)

While it doesn't make a difference from a Strapp perspective, keeping a strict barrier between
the click cli structure and the actual code which performs the actions of the cli tends to make
testing much easier, tests just need to produce test-stubs for the arguments rather than
needing to interact with click's testing facilities.

Testing
-------

We also include a testing module to reduce to boilerplate associated with testing cli commands.

.. automodule:: strapp.click.testing
    :members: ClickRunner, ClickResult

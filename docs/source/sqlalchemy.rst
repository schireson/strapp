SQLAlchemy
==========

Model Base
----------

The :func:`declarative_base` function, allows you to very concisely opt into two columns
which are very commonly included on a majority of tables, :code:`created_at` and :code`updated_at`.

.. automodule:: strapp.sqlalchemy
    :members: declarative_base


Session
-------

.. automodule:: strapp.sqlalchemy
    :members: create_session

Configly Integration
~~~~~~~~~~~~~~~~~~~~
The :code:`config` argument accepts :class:`URL <sqlalchemy.engine.url.URL>` arguments
as a :class:`typing.Mapping`, in order to make usage with Configly more straightforward.

Applications might define their configuration using configly.

.. code-block:: yaml
   :caption: config.yml

   ...
   database:
     drivername: postgesql+postgres
     host: <% ENV[DATABASE_HOST] %>
     username: <% ENV[DATABASE_USERNAME] %>
     ... etc ...
   ...


Then a typical strapp :ref:`Flask` app would construct a config instance once before app startup,
and use that to hook up their database to the flask app.

.. code-block:: python
   :caption: wsgi.py

   from configly import Config
   from strapp.flask import database_callback, sqlalchemy_database

   config = Configly.from_yaml('config.yml')
   callback = database_callback(sqlalchemy_database, config.database)
   app = create_app(callbacks=[callback])


And a typical strapp :ref:`Click` app, might use the resolver and produce the engine that way.

.. code-block:: python
   :caption: cli.py

   from strapp.click import Resolver
   from configly import Config

   def config():
       return Config.from_yaml("config.yml")

    def postgres(config):
        return strapp.sqlalchemy.create_session(config.database)

   resolver = Resolver(config=config, postgres=postgres)

   @resolver.group()
   def command(postgres):
       ...

In neither case are you required to actually use Configly, but it is intentionally easy to do!

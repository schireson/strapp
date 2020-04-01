Flask
=====

A key annoyance with how flask typically recommends your applications be set up
is that things like your :code:`app` instance, plugins, database handles,
etc tend to be module-level attributes and it's tempting or even encouraged
to import and use them in code elsewhere (which often leads to gnarnly circular
import issues).

The pattern that Strapp tries to encourage, encapsulates as much of that
as possible, so that the "only" (read easy/obvious) way to do things
avoids these problems entirely.

Setup
-----

.. automodule:: strapp.flask
    :members: create_app

A typical :code:`ls` of a project directory might look something like

.. code-block::

   app.py (generally, either this or __main__.py, and not both)
   src/
       project/
           __main__.py
           routes.py
           errors.py
           views/
               ...
           ...

All app setup, and references to things like plugins, and config are encouraged
to exist in either something like the :code:`app.py` above, or the :code:`__main__.py`. The idea being that its location encourages you to **not** try to import it.

There your file contents might look like so:

.. code-block:: python
   :caption: app.py or __main__.py

   from configly import Config
   from setuplog import setup_logging
   from strapp.flask import create_app, callback_factory, default_error_handlers, handler_exception, sqlalchemy_database

   from project.routes import routes
   from project.errors import CustomErrorType

   config = Config.from_yaml('config.yml')

   setup_logging(**config.logging.to_dict())

   app = create_app(
       routes,
       config=config.flask,
       error_handlers=[
           *default_error_handlers,
           handler_exception(CustomErrorType),
       ],
       plugins=[
           # FlaskCORS(),
           # FlaskWhateverPlugin(),
       ]
       callbacks=[
           callback_factory(sqlalchemy_database, config.database)
       ),
    )


A couple of notes:

* As we'll see below, routes can be directly imported because the :code:`routes`
  argument does not require a reference to :code:`app` (as it would normally, though,
  you **can** always put this somewhere importable and do route setup in a more typical way).

* the intent is to centralize and pre-instantiate any shared objects which
  views might otherwise try to import, and make them available to views through
  means other than direct import.

* This callback mechanism, (along with :func:`strapp.flask.inject_db` below), are recommended
  rather than using e.g. FlaskSQLAlchemy (which encourages and/or requires a circular dependence
  of your models on a flask-specific plugin), though once again you can use whatever you'd like.

.. automodule:: strapp.flask.database
    :members: callback_factory, sqlalchemy_database



Routes
------

.. code-block:: python
   :caption: routes.py

   from strapp.flask import Route

   from project.views import x, bar

   routes = [
       ('GET', '/foo', x.get_x),
       Route.to('POST', '/bar', y.create_bar, endpoint='create_bar'),
       dict(method='GET', path='/foo', view=x.get_x),
   ]

We try to be as flexible as possible in allowing the routes to be defined concisely. Ultimately,
all the arguments boil down to the arguments sent into :meth:`flask.Flask.route`, however
the actual reference (and attachment) to the app is delayed until the call to :func:`strapp.flask.create_app`.


.. automodule:: strapp.flask.route
    :members: Route


Views
-----

Finally, for defining actual view functions, there are additional decorators which
can be used to simplify a typical (usually json) route.

.. automodule:: strapp.flask.decorators
    :members: inject, inject_db, manage_session, json_response

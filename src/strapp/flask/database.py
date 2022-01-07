from typing import Mapping

import flask
import werkzeug


def sqlalchemy_database(app: flask.Flask, config: Mapping):
    """Produce a session, for use in the context of a flask request response cycle.

    Typically this would be used in conjunction with :func:`strapp.flask.callback_factory`.
    """
    from strapp.sqlalchemy import create_session_cls

    if werkzeug.__version__.startswith("2.1"):
        scopefunc = flask._app_ctx_stack.__ident_func__
    else:
        scopefunc = None

    Session = create_session_cls(config, scopefunc=scopefunc)
    session = Session()

    @app.teardown_appcontext
    def shutdown_session(response_or_exc):
        """Ensure that the session is removed on app context teardown.
        """
        Session.remove()
        return response_or_exc

    return session


def callback_factory(db_func, config: Mapping, *, key):
    """Attach a given callback to the flask app as an "extension".

    Typically this would be used in conjunction with :func:`strapp.flask.inject`.

    Examples:
        >>> from strapp.flask import create_app
        >>> config = {'drivername': 'sqlite'}
        >>> callback = callback_factory(sqlalchemy_database, config, key='db')
        >>> app = create_app(callbacks=[callback])
    """

    def callback(app: flask.Flask):
        session = db_func(app, config)
        app.extensions[key] = session

    return callback

from typing import Mapping, Optional

import flask
from flask_reverse_proxy import FlaskReverseProxied

from strapp.flask.error import default_error_handlers
from strapp.flask.route import Route


def register_error_handlers(app, error_handlers):
    for error_cls, handler_fn in error_handlers:
        app.register_error_handler(error_cls, handler_fn)


def register_routes(app, routes):
    for route in routes:
        route = Route.parse(route)
        decorator = app.route(
            route.path, methods=route.methods, endpoint=route.endpoint, **route.kwargs
        )
        decorator(route.view)


def register_plugins(app, plugins, *, proxied=True):
    if proxied:
        proxied = FlaskReverseProxied()
        plugins = plugins + [proxied]

    for plugin in plugins:
        plugin.init_app(app)


def create_app(
    routes=None,
    *,
    config: Optional[Mapping] = None,
    plugins=None,
    error_handlers=None,
    flask_args=None,
    proxied=True,
    callbacks=None
):
    """Create a flask app instance.

    Args:
        routes: Optional list of routes to attach to the flask app.
        config: Optional configuration to apply to the flask app instance.
        plugins: Optional list of `Flask` plugins to attach to the flask app instance (calls,
            :code:`plugin.init_app` on each plugin)
        error_handlers: Optional list of error handlers to register. Defaults to
            :attr:`default_error_handlers`, which handles all strapp's predefined errors.
        flask_args: Optional set of kwargs to pass through to the `Flask` constructor.
        proxied: Whether to apply a flask middleware which allows it to be proxied through nginx.
        callbacks: Optional list of functions which accept an `app` instance as their only argument.

    Examples:
        Registering routes:

        >>> routes = [
        ...     Route.to('GET', '/four', lambda: 4),
        ...     ('GET', '/five', lambda: 5),
        ...     ('GET', '/six', lambda: 6, {'endpoint': 'siiiixxxxxx'}),
        ...     dict(method='GET', path='/seven', view=lambda: 7),
        ... ]
        >>> create_app(routes)
        <Flask '...'>

        Specifying config

        >>> create_app(config={'FLASK_DEBUG': True})
        <Flask '...'>

        Specifying registering non-default error handlers

        >>> from strapp.flask import handle_exception, BadRequest
        >>> error_handlers = [
        ...     handle_exception(BadRequest),
        ...     handle_exception(Exception, include_traceback=True),
        ... ]
        >>> create_app(error_handlers=error_handlers)
        <Flask '...'>

        Specifying flask construction arguments.

        >>> create_app(flask_args={'template_folder': '.'})
        <Flask '...'>

        Adding non-plugin, things which require access to the app, such as registering a database.

        >>> from strapp.flask import callback_factory, sqlalchemy_database
        >>> config = {'drivername': 'sqlite'}
        >>> callbacks = [
        ...     callback_factory(sqlalchemy_database, config, key='db')
        ... ]
        >>> create_app(callbacks=callbacks)
        <Flask '...'>
    """
    routes = routes or []
    plugins = plugins or []
    error_handlers = error_handlers or default_error_handlers
    flask_args = flask_args or {}
    callbacks = callbacks or []

    app = flask.Flask(__name__, **flask_args)
    app.config.update(**(config or {}))

    register_error_handlers(app, error_handlers)
    register_routes(app, routes)
    register_plugins(app, plugins, proxied=proxied)

    for callback in callbacks:
        callback(app)

    return app

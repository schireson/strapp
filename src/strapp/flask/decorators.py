import contextlib
import functools

import flask


def manage_session(commit_on_success=False):
    """Create a context manager which manages the lifecycle of a sqlalchemy session.

    See :func:`strapp.flask.inject`.

    Args:
        commit_on_success: By default, changes are rolledback. If :code:`True`, changes will
            be committed.
    """

    @contextlib.contextmanager
    def _manage_session(db):
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        else:
            if commit_on_success:
                db.commit()
            db.close()

    return _manage_session


def identity():
    """Create a context manager which **just** yields the extension.

    Directly yields the extension without additional behavior. See :func:`strapp.flask.inject`.

    Examples:
        >>> @inject(db=identity())
        ... def view(db):
        ...     ...
    """

    @contextlib.contextmanager
    def _manage(extension):
        yield extension

    return _manage


def inject(**injections):
    """Inject context managed extensions into the view.

    Args:
        **injections: A mapping from the name of an extension, to a context-manager function
            which knows how to manage that extension within the context of a request.

    Examples:
        Given a known extension, such as a database mounted to key "db"

        >>> from strapp.flask import callback_factory, create_app, sqlalchemy_database
        >>> config = {'drivername': 'sqlite'}
        >>> app = create_app(callbacks=[callback_factory(sqlalchemy_database, config, key='db')])

        Inject that extension into the view under the keyword argument's name, routed through
        the context management function (i.e. the value).

        >>> @inject(db=manage_session(commit_on_success=True))
        ... def view(db):
        ...    ...
    """

    def _inject(fn_):
        @functools.wraps(fn_)
        def wrapper(**kwargs):
            with contextlib.ExitStack() as stack:
                injected_kwargs = {}
                for key, injection in injections.items():
                    try:
                        extension = flask.current_app.extensions[key]
                    except KeyError:
                        raise ValueError(f"{key} is not registered in flask's extensions.")
                    injected_kwargs[key] = stack.enter_context(injection(extension))

                result = fn_(**kwargs, **injected_kwargs)
            return result

        return wrapper

    return _inject


def inject_db(fn=None, *, commit_on_success=False, key="db"):
    """Shortcut to :code:`@inject(db=manage_session(...))`, to inject and manage database sessions.

    Args:
        fn: Used for argumentless-syntax.
        commit_on_success: By default, changes are rolledback. If :code:`True`, changes will
            be committed.
        key: The flask "extension" key to pull the session from. This should match use of
            the :code:`key` from i.e. :func:`strapp.flask.callback_factory`.

    Examples:
        >>> @inject_db
        ... def view(db):
        ...     pass
        >>>
        >>> @inject_db(commit_on_success=True)
        ... def post_endpoint_example(db):
        ...     pass
    """

    def _inject_db(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            manager = manage_session(commit_on_success=commit_on_success)
            db = flask.current_app.extensions[key]
            with manager(db) as db:
                result = fn(db, *args, **kwargs)
            return result

        return wrapper

    if fn is not None:
        return _inject_db(fn)
    return _inject_db


def json_response(fn=None, status=200, headers=None):
    """Automatically coerces a json serializable return value into an actual json response.

    Args:
        fn: Used for argumentless-syntax.
        status: The status code of the response (default 200)
        headers: Additional headers to include in the response response

    Examples:
        >>> @json_response
        ... def view():
        ...     pass

        >>> @json_response(status=201, headers={})
        ... def view():
        ...     pass
    """
    headers = headers or {}

    def _json_response(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            body = flask.jsonify(result)

            headers.update({"ContentType": "application/json"})
            return flask.make_response((body, status, headers))

        return wrapper

    if fn is not None:
        return _json_response(fn)
    return _json_response

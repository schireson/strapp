import flask


def sqlalchemy_database(app: flask.Flask, config: dict):
    from strapp.sqlalchemy import create_session_cls

    Session = create_session_cls(config, scopefunc=flask._app_ctx_stack.__ident_func__)
    session = Session()

    @app.teardown_appcontext
    def shutdown_session(response_or_exc):
        """Ensure that the session is removed on app context teardown.
        """
        Session.remove()
        return response_or_exc

    return session


def database_callback(db_func, config: dict, extension_key="db"):
    def callback(app: flask.Flask):
        session = db_func(app, config)
        app.extensions[extension_key] = session

    return callback

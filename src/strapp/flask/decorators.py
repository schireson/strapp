import functools

import flask


def inject_db(fn=None, *, commit_on_success=False, extension_key="db"):
    def _inject_db(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            db = flask.current_app.extensions[extension_key]

            try:
                result = fn(db, *args, **kwargs)
            except Exception:
                db.rollback()
                raise
            else:
                if commit_on_success:
                    db.commit()
                db.close()

            return result

        return wrapper

    if fn is not None:
        return _inject_db(fn)
    return _inject_db


def json_response(fn=None, status=200, headers=None):
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

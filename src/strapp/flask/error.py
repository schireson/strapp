import abc
import json
import logging
import traceback

import werkzeug
from flask import Response

try:
    import sentry_sdk
except ImportError:  # pragma: nocover
    sentry_sdk = None  # type: ignore


log = logging.getLogger(__name__)


class HTTPException(werkzeug.exceptions.HTTPException, metaclass=abc.ABCMeta):
    """Common base class on which `strapp` users should base any custom error responses with.
    """

    def __init__(self, description=None):
        self.description = description or self.description
        super().__init__()

    @property
    @abc.abstractmethod
    def code(self):
        """Override this property with a real status code value.

        Examples:
            >>> class TeacupError(HTTPException):
            ...     code = 418
        """

    @property
    @abc.abstractmethod
    def description(self):
        """Override this property with a real description of the error.

        Examples:
            >>> class TeacupError(HTTPException):
            ...     description = "I'm a teapot"
        """


def handle_exception(cls, include_traceback=False):
    """Generate a exception handling callback pair for consumption by `create_app`.

    Args:
        cls: The exception cls type to apply an exception handler for.
        include_traceback: Optional option to include a `traceback` key in the error response.

    Examples:
        >>> error_handlers = [
        ...     handle_exception(BadRequest),
        ...     handle_exception(Exception, include_traceback=True),
        ... ]
        >>> # create_app(error_handlers=error_handlers)
    """

    def handler(error):
        if isinstance(error, HTTPException):
            body = {"error": error.description}
        else:
            body = {"error": "({}) {}".format(type(error).__name__, error)}

        if include_traceback:
            traceback_list = _get_traceback_list(error)
            body["traceback"] = traceback_list

            log.info("\n".join(traceback_list))

            if sentry_sdk:
                sentry_sdk.capture_exception(error)

        status_code = 500
        if isinstance(error, werkzeug.exceptions.HTTPException):
            status_code = error.code

        return Response(json.dumps(body), status=status_code, mimetype="application/json")

    return cls, handler


class BadRequest(HTTPException):
    code = 400
    description = "Bad Request"


class UnprocessableEntity(HTTPException):
    code = 422
    description = "The request was well-formed but had semantic errors/inconsistencies"


class InternalError(HTTPException):
    code = 500
    description = "Internal Error"


default_error_handlers = [
    handle_exception(BadRequest),
    handle_exception(UnprocessableEntity),
    handle_exception(InternalError),
    handle_exception(werkzeug.exceptions.HTTPException),
    handle_exception(Exception, include_traceback=True),
]


def _get_traceback_list(exception):
    traceback_list = traceback.TracebackException.from_exception(exception).format()
    traceback_str = "".join(traceback_list)
    return traceback_str.split("\n")

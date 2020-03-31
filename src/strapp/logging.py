import logging

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR


_log = logging.getLogger(__name__)


def package_verbosity_factory(*definitions):
    """Describe per-package verbosity.

    Each `definitions` item should be an iterable which describes the progression of log level
    at each level of verbosity.

    Examples:
        This states that: `urllib3` should start at INFO logs by default, then only increase to
        DEBUG at 3 verbosity (i.e. -vvv). And that `sqlalchemy` should start at WARNING, then
        INFO (at -v), and DEBUG (at -vv, -vvv, etc)

        >>> package_verbosity = package_verbosity_factory(
        ...     ("urllib3", logging.INFO, logging.INFO, logging.INFO, logging.DEBUG),
        ...     ("sqlalchemy", logging.WARNING, logging.INFO, logging.DEBUG),
        ... )
        >>> package_verbosity(0)
        {'urllib3': 20, 'sqlalchemy': 30}
        >>> package_verbosity(1)
        {'urllib3': 20, 'sqlalchemy': 20}
        >>> package_verbosity(2)
        {'urllib3': 20, 'sqlalchemy': 10}
        >>> package_verbosity(3)
        {'urllib3': 10, 'sqlalchemy': 10}

        Omitting the log level progression entirely isn't really an intended usecase, but
        the returned callable accepts a `default` arg, which can be used to control the
        behavior in this case. It defaults to `logging.INFO`

        >>> package_verbosity = package_verbosity_factory(["urllib3"])
        >>> package_verbosity(0)
        {'urllib3': 20}

        >>> package_verbosity(0, default=logging.DEBUG)
        {'urllib3': 10}

    Returns:
        A callable which, given the desired `verbosity`, returns a mapping of package to log level.
    """

    def package_verbosity(verbosity, default=logging.INFO):
        result = {}
        for package, *levels in definitions:
            level = min(len(levels) - 1, verbosity)
            try:
                log_level = levels[level]
            except IndexError:
                _log.warning("Did not specify %s log levels for %s", verbosity, package)
                log_level = default

            result[package] = log_level
        return result

    return package_verbosity

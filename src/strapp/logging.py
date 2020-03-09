import logging

import setuplog


def setup_logging(level, verbosity: int):
    """Setup app logging.

    It's expected that this function is called once at app startup.
    """
    package_verbosity = {
        "urllib3": (3, logging.INFO),
        "sqlalchemy.engine": (3, logging.WARNING),
        "docker": (3, logging.INFO),
    }
    setuplog.setup_logging(
        log_level_overrides={
            package: logging.DEBUG if verbosity >= limit else non_verbose_level
            for package, (limit, non_verbose_level) in package_verbosity.items()
        }
    )

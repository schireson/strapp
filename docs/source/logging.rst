Logging
=======

.. automodule:: strapp.logging
    :members: package_verbosity_factory

This is **most** useful when paired with setuplog_ or loguru_.

* Setuplog's :func:`setup_logging` accepts a :code:`log_level_overrides` argument who's format
  matches the output of this function.
* Loguru's :func:`loguru.add` function accepts a :code:`filter` argument which who's format is
  compatible with the output of this function.


For use in applications, it's generally useful to call this as early as it is possible to have
the level of verbosity you want.

For cli applications, this will tend to be inside the root cli group, where you accept the verbosity
level.

.. code-block:: python

   import logging
   import strapp.logging
   from setuplog import setup_logging

   package_verbosity = strapp.logging.package_verbosity_factory(
       ("urllib3", logging.INFO, logging.INFO, logging.INFO, logging.DEBUG),
       ("sqlalchemy.engine", logging.WARNING, logging.WARNING, logging.INFO, logging.DEBUG),
       ("docker", logging.INFO, logging.INFO, logging.INFO, logging.DEBUG),
   )

   @click.group()
   @click.option('--verbose', count=True, default=0)
   def cli(verbose):
       setup_logging(
           config.logging.level, log_level_overrides=package_verbosity(verbose),
       )

For flask apps, this tends to be even earlier, i.e. as soon as you load the config.

.. _loguru: https://loguru.readthedocs.io
.. _setuplog: https://setuplog.readthedocs.io

![Github Actions Build](https://github.com/schireson/databudgie/actions/workflows/build.yml/badge.svg) [![codecov](https://codecov.io/gh/schireson/strapp/branch/main/graph/badge.svg)](https://codecov.io/gh/schireson/strapp) [![Documentation Status](https://readthedocs.org/projects/strapp/badge/?version=latest)](https://strapp.readthedocs.io/en/latest/?badge=latest)

# Strapp

A mildly opinionated library used to boot**str**ap **app**s. Its primary use is to commonize
(and test) the typical bespoke boilerplate most applications tend to reimplement to
varying levels of sophistication.

All dependencies are intentionally optional, and exposed through extras in order to make
opting into or out of specific strapp decisions and modules entirely optional.

## Package Highlights

- [SQLAlchemy](https://strapp.readthedocs.io/latest/sqlalchemy.html)

  - Session creation helper functions
    - Opt-in "dry run" session feature
  - Custom `declarative_base`

    - Opt-in created_at/updated_at columns
    - Opt-out `repr`able models
    - For type safety, utilize the mypy plugin

      ```toml
      [tool.mypy]
      plugins = 'strapp.sqlalchemy.mypy'
      ```

- [Click](https://strapp.readthedocs.io/latest/click.html)

  - Context "Resolver"

- [Flask](https://strapp.readthedocs.io/latest/flask.html)

  - Non-decorator based route registration pattern (removes circular import issues)
  - Opt-in error handlers
  - Opt-in database handling

- [Logging](https://strapp.readthedocs.io/latest/logging.html)

  - Logging verbosity helper

- [Sentry](https://strapp.readthedocs.io/latest/sentry.html)

  - Setup helper
  - Context helper

- [Dramatiq](https://strapp.readthedocs.io/latest/dramatiq.html)
  - Interface helpers (`configure`, `enqueue`, `get_results`)
  - Declarative actors (`PreparedActor`)
  - Optional middlewares: `SentryMiddleware`, `DatadogMiddleware`

## Optional Integrations

Strapp is designed with integration with [Configly](https://configly.readthedocs.org/latest) and
[Setuplog](https://setuplog.readthedocs.org/latest), two of our other open sourced packages.

These are entirely optional, and explained at the relevant locations in the docs
to which they apply.

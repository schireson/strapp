# flake8: noqa
from strapp.sqlalchemy.model_base import declarative_base
from strapp.sqlalchemy.session import create_session

try:
    import pytest
except ImportError:  # pragma: nocover
    pass
else:
    pytest.register_assert_rewrite("strapp.sqlalchemy.testing")
    del pytest

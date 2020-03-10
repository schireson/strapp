# flake8: noqa
from strapp.sqlalchemy.model_base import declarative_base

try:
    import pytest
except ImportError:
    pass
else:
    pytest.register_assert_rewrite("strapp.sqlalchemy.testing")

# flake8: noqa
from strapp.sqlalchemy.model_base import declarative_base, DeclarativeMeta
from strapp.sqlalchemy.session import create_session, create_session_cls

try:
    import pytest
except ImportError:  # pragma: nocover
    pass
else:
    pytest.register_assert_rewrite("strapp.sqlalchemy.testing")
    del pytest

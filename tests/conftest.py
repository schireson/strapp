import pytest


@pytest.fixture
def responses():
    import responses

    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps

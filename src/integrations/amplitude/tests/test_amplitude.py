from unittest import mock

from pytest import fail


@mock.patch("integrations.amplitude.amplitude.requests")
def test_identify_user(mock_requests):
    # TODO: implement me
    fail()

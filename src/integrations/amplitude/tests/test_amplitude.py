from unittest import mock, SkipTest

from pytest import fail


@SkipTest
@mock.patch("integrations.amplitude.amplitude.requests")
def test_identify_user(mock_requests):
    # TODO: implement me
    fail()

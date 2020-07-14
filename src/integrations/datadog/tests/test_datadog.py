from unittest import mock

from pytest import fail


# TODO: look into using https://github.com/betamaxpy/betamax or https://github.com/getsentry/responses
@mock.patch("integrations.datadog.datadog.requests")
def test_datadog_track_event(mock_requests):
    # TODO: implement me
    fail()


def test_datadog_generate_event_data():
    # TODO: implement me
    fail()

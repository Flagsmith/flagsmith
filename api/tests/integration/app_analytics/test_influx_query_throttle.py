from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient


def test_influx_data_endpoint_is_throttled(
    admin_client: APIClient,
    organisation: int,
    mocker: MockerFixture,
    reset_cache: None,
) -> None:
    # Given
    mocker.patch(
        "app_analytics.throttles.InfluxQueryThrottle.get_rate", return_value="1/minute"
    )
    mocker.patch(
        "organisations.views.get_multiple_event_list_for_organisation", return_value=[]
    )

    url = reverse(
        "api-v1:organisations:organisation-get-influx-data",
        args=[organisation],
    )

    # When - first request should be successful
    first_response = admin_client.get(url)
    second_response = admin_client.get(url)

    # Then
    # The first response should have been successful
    assert first_response.status_code == status.HTTP_200_OK

    # But the second request should have been throttled
    assert second_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

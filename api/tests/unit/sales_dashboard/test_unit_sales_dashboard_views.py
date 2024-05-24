import pytest
from django.test import RequestFactory
from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework.test import APIClient

from organisations.models import (
    Organisation,
    OrganisationSubscriptionInformationCache,
)
from sales_dashboard.views import OrganisationList


@pytest.mark.parametrize(
    "allowed_calls_30d, actual_calls_30d, expected_overage",
    ((1000000, 500000, 0), (1000000, 1100000, 100000), (0, 100000, 100000)),
)
def test_organisation_subscription_get_api_call_overage(
    organisation: Organisation,
    allowed_calls_30d: int,
    actual_calls_30d: int,
    expected_overage: int,
) -> None:
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_30d_api_calls=allowed_calls_30d,
        api_calls_30d=actual_calls_30d,
    )

    request = RequestFactory().get("/sales-dashboard")
    view = OrganisationList()
    view.request = request
    result = view.get_queryset().get(pk=organisation.id)

    assert result.overage == expected_overage


def test_get_organisation_info__get_event_list_for_organisation(
    organisation: Organisation,
    superuser_client: APIClient,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.INFLUXDB_TOKEN = "AFancyToken"

    url = reverse("sales_dashboard:organisation_info", args=[organisation.id])

    event_list_mock = mocker.patch(
        "sales_dashboard.views.get_event_list_for_organisation"
    )
    event_list_mock.return_value = (
        {"traits": [], "identities": [], "flags": [], "environment-document": []},
        ["label1", "label2"],
    )
    mocker.patch("sales_dashboard.views.get_events_for_organisation")

    # When
    response = superuser_client.get(url)

    # Then
    assert "label1" in str(response.content)
    assert "label2" in str(response.content)
    event_list_mock.assert_called_once_with(organisation.id, "-180d", "now()")

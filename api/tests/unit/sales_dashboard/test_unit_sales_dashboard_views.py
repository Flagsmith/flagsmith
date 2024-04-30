import pytest
from django.test import RequestFactory

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

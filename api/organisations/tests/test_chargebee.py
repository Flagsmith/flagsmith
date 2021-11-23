from datetime import datetime
from unittest import TestCase, mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pytz import UTC

from organisations.chargebee import (
    get_customer_id_from_subscription_id,
    get_hosted_page_url_for_existing_subscription,
    get_max_seats_for_plan,
    get_portal_url,
    get_subscription_data_from_hosted_page,
)


class MockChargeBeePlanResponse:
    def __init__(self, max_seats=0):
        self.max_seats = max_seats
        self.plan = MockChargeBeePlan(max_seats)


class MockChargeBeePlan:
    def __init__(self, max_seats=0):
        self.meta_data = {"seats": max_seats}


class MockChargeBeeHostedPageResponse:
    def __init__(
        self,
        subscription_id="subscription-id",
        plan_id="plan-id",
        created_at=datetime.utcnow(),
        customer_id="customer-id",
    ):
        self.hosted_page = MockChargeBeeHostedPage(
            subscription_id=subscription_id,
            plan_id=plan_id,
            created_at=created_at,
            customer_id=customer_id,
        )


class MockChargeBeeHostedPage:
    def __init__(
        self,
        subscription_id,
        plan_id,
        created_at,
        customer_id,
        hosted_page_id="some-id",
    ):
        self.id = hosted_page_id
        self.content = MockChargeBeeHostedPageContent(
            subscription_id=subscription_id,
            plan_id=plan_id,
            created_at=created_at,
            customer_id=customer_id,
        )


class MockChargeBeeHostedPageContent:
    def __init__(self, subscription_id, plan_id, created_at, customer_id):
        self.subscription = MockChargeBeeSubscription(
            subscription_id=subscription_id, plan_id=plan_id, created_at=created_at
        )
        self.customer = MockChargeBeeCustomer(customer_id)


class MockChargeBeeSubscriptionResponse:
    def __init__(
        self,
        subscription_id="subscription-id",
        plan_id="plan-id",
        created_at=datetime.now(),
        customer_id="customer-id",
    ):
        self.subscription = MockChargeBeeSubscription(
            subscription_id, plan_id, created_at
        )
        self.customer = MockChargeBeeCustomer(customer_id)


class MockChargeBeeSubscription:
    def __init__(self, subscription_id, plan_id, created_at):
        self.id = subscription_id
        self.plan_id = plan_id
        self.created_at = datetime.timestamp(created_at)


class MockChargeBeeCustomer:
    def __init__(self, customer_id):
        self.id = customer_id


class MockChargeBeePortalSessionResponse:
    def __init__(self, access_url="https://test.portal.url"):
        self.portal_session = MockChargeBeePortalSession(access_url)


class MockChargeBeePortalSession:
    def __init__(self, access_url):
        self.access_url = access_url


@pytest.mark.django_db
class ChargeBeeTestCase(TestCase):
    def setUp(self) -> None:
        monkeypatch = MonkeyPatch()
        self.mock_cb = mock.MagicMock()

        monkeypatch.setattr("organisations.chargebee.chargebee", self.mock_cb)

    def test_get_max_seats_for_plan_returns_max_seats_for_plan(self):
        # Given
        plan_id = "startup"
        expected_max_seats = 3

        self.mock_cb.Plan.retrieve.return_value = MockChargeBeePlanResponse(
            expected_max_seats
        )

        # When
        max_seats = get_max_seats_for_plan(plan_id)

        # Then
        assert max_seats == expected_max_seats

    def test_get_subscription_data_from_hosted_page_returns_expected_values(self):
        # Given
        subscription_id = "abc123"
        plan_id = "startup"
        expected_max_seats = 3
        created_at = datetime.now(tz=UTC)
        customer_id = "customer-id"

        self.mock_cb.HostedPage.retrieve.return_value = MockChargeBeeHostedPageResponse(
            subscription_id=subscription_id,
            plan_id=plan_id,
            created_at=created_at,
            customer_id=customer_id,
        )
        self.mock_cb.Plan.retrieve.return_value = MockChargeBeePlanResponse(
            expected_max_seats
        )

        # When
        subscription_data = get_subscription_data_from_hosted_page("hosted_page_id")

        # Then
        assert subscription_data["subscription_id"] == subscription_id
        assert subscription_data["plan"] == plan_id
        assert subscription_data["max_seats"] == expected_max_seats
        assert subscription_data["subscription_date"] == created_at
        assert subscription_data["customer_id"] == customer_id

    def test_get_portal_url(self):
        # Given
        access_url = "https://test.url.com"

        self.mock_cb.PortalSession.create.return_value = (
            MockChargeBeePortalSessionResponse(access_url)
        )

        # When
        portal_url = get_portal_url("some-customer-id", "https://redirect.url.com")

        # Then
        assert portal_url == access_url

    def test_get_customer_id_from_subscription(self):
        # Given
        expected_customer_id = "customer-id"
        self.mock_cb.Subscription.retrieve.return_value = (
            MockChargeBeeSubscriptionResponse(customer_id=expected_customer_id)
        )

        # When
        customer_id = get_customer_id_from_subscription_id("subscription-id")

        # Then
        assert customer_id == expected_customer_id

    def test_get_hosted_page_url_for_existing_subscription(self):
        # Given
        subscription_id = "test-id"

        # When
        response = get_hosted_page_url_for_existing_subscription(subscription_id)

        # Then
        assert response
        self.mock_cb.HostedPage.checkout_existing.assert_called_once_with(
            params={"subscription": {"id": subscription_id}}
        )

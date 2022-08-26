from datetime import datetime
from unittest import TestCase, mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from chargebee import APIError
from pytz import UTC

from organisations.chargebee import (
    get_customer_id_from_subscription_id,
    get_hosted_page_url_for_subscription_upgrade,
    get_max_api_calls_for_plan,
    get_max_seats_for_plan,
    get_plan_meta_data,
    get_portal_url,
    get_subscription_data_from_hosted_page,
    get_subscription_metadata,
)
from organisations.chargebee.chargebee import cancel_subscription
from organisations.subscriptions.exceptions import (
    CannotCancelChargebeeSubscription,
)


class MockChargeBeePlanResponse:
    def __init__(self, max_seats=0, max_api_calls=50000):
        self.max_seats = max_seats
        self.max_api_calls = 50000
        self.plan = MockChargeBeePlan(max_seats, max_api_calls)


class MockChargeBeePlan:
    def __init__(self, max_seats=0, max_api_calls=50000):
        self.meta_data = {"seats": max_seats, "api_calls": max_api_calls}


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


class ChargeBeeTestCase(TestCase):
    def setUp(self) -> None:
        monkeypatch = MonkeyPatch()
        self.mock_cb = mock.MagicMock()

        monkeypatch.setattr("organisations.chargebee.chargebee.chargebee", self.mock_cb)

    def test_get_max_seats_for_plan_returns_max_seats_for_plan(self):
        # Given
        meta_data = {"seats": 3, "api_calls": 50000}

        # When
        max_seats = get_max_seats_for_plan(meta_data)

        # Then
        assert max_seats == meta_data["seats"]

    def test_get_max_api_calls_for_plan_returns_max_api_calls_for_plan(self):
        # Given
        meta_data = {"seats": 3, "api_calls": 50000}

        # When
        max_api_calls = get_max_api_calls_for_plan(meta_data)

        # Then
        assert max_api_calls == meta_data["api_calls"]

    def test_get_plan_meta_data_returns_correct_metadata(self):
        # Given
        plan_id = "startup"
        expected_max_seats = 3
        expected_max_api_calls = 50

        self.mock_cb.Plan.retrieve.return_value = MockChargeBeePlanResponse(
            expected_max_seats, expected_max_api_calls
        )

        # When
        plan_meta_data = get_plan_meta_data(plan_id)

        # Then
        assert plan_meta_data == {
            "api_calls": expected_max_api_calls,
            "seats": expected_max_seats,
        }
        self.mock_cb.Plan.retrieve.assert_called_with(plan_id)

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

    def test_get_hosted_page_url_for_subscription_upgrade(self):
        # Given
        subscription_id = "test-id"
        plan_id = "plan-id"
        url = "https://some.url.com/some/page/"
        self.mock_cb.HostedPage.checkout_existing.return_value = mock.MagicMock(
            hosted_page=mock.MagicMock(url=url)
        )

        # When
        response = get_hosted_page_url_for_subscription_upgrade(
            subscription_id, plan_id
        )

        # Then
        assert response == url
        self.mock_cb.HostedPage.checkout_existing.assert_called_once_with(
            {"subscription": {"id": subscription_id, "plan_id": plan_id}}
        )


@pytest.mark.parametrize("addon_quantity", (None, 1))
def test_get_subscription_metadata(mocker, chargebee_object_metadata, addon_quantity):
    # Given
    plan_id = "plan-id"
    addon_id = "addon-id"
    subscription_id = "subscription-id"

    # Let's create a (mocked) subscription object
    mocked_subscription = mocker.MagicMock(
        id=subscription_id,
        plan_id=plan_id,
        addons=[mocker.MagicMock(id=addon_id, quantity=addon_quantity)],
    )
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")

    # tie that subscription object to the mocked chargebee object
    mocked_chargebee.Subscription.retrieve.return_value.subscription = (
        mocked_subscription
    )

    # now, let's mock chargebee cache object
    mocked_chargebee_cache = mocker.patch(
        "organisations.chargebee.chargebee.ChargebeeCache", autospec=True
    )
    mocked_chargebee_cache.return_value.plans = {plan_id: chargebee_object_metadata}
    mocked_chargebee_cache.return_value.addons = {addon_id: chargebee_object_metadata}

    # When
    subscription_metadata = get_subscription_metadata(subscription_id)

    # Then
    assert subscription_metadata.seats == chargebee_object_metadata.seats * 2
    assert subscription_metadata.api_calls == chargebee_object_metadata.api_calls * 2
    assert subscription_metadata.projects == chargebee_object_metadata.projects * 2


def test_cancel_subscription(mocker):
    # Given
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")
    subscription_id = "sub-id"

    # When
    cancel_subscription(subscription_id)

    # Then
    mocked_chargebee.Subscription.cancel.assert_called_once_with(
        subscription_id, {"end_of_term": True}
    )


def test_cancel_subscription_throws_cannot_cancel_error_if_api_error(mocker, caplog):
    # Given
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")
    subscription_id = "sub-id"

    # Chargebee's APIError requires additional arguments to instantiate it so instead
    # we mock it with our own exception here to test that it is caught correctly
    class MockException(Exception):
        pass

    mocker.patch("organisations.chargebee.chargebee.APIError", MockException)

    mocked_chargebee.Subscription.cancel.side_effect = MockException

    # When
    with pytest.raises(CannotCancelChargebeeSubscription):
        cancel_subscription(subscription_id)

    # Then
    mocked_chargebee.Subscription.cancel.assert_called_once_with(
        subscription_id, {"end_of_term": True}
    )
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert (
        caplog.records[0].message
        == "Cannot cancel CB subscription for subscription id: %s" % subscription_id
    )


def test_get_subscription_metadata_returns_null_if_chargebee_error(
    mocker, chargebee_object_metadata
):
    # Given
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")
    mocked_chargebee.Subscription.retrieve.side_effect = APIError(
        http_code=200, json_obj=mocker.MagicMock()
    )

    subscription_id = "foo"  # arbitrary subscription id

    # When
    subscription_metadata = get_subscription_metadata(subscription_id)

    # Then
    assert subscription_metadata is None

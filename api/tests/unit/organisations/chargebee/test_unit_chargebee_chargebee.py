from datetime import datetime
from unittest import mock

import pytest
from _pytest.monkeypatch import MonkeyPatch
from chargebee import APIError
from pytz import UTC

from organisations.chargebee import (
    add_single_seat,
    extract_subscription_metadata,
    get_customer_id_from_subscription_id,
    get_hosted_page_url_for_subscription_upgrade,
    get_max_api_calls_for_plan,
    get_max_seats_for_plan,
    get_plan_meta_data,
    get_portal_url,
    get_subscription_data_from_hosted_page,
    get_subscription_metadata_from_id,
)
from organisations.chargebee.chargebee import cancel_subscription
from organisations.chargebee.constants import ADDITIONAL_SEAT_ADDON_ID
from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.subscriptions.exceptions import (
    CannotCancelChargebeeSubscription,
    UpgradeSeatsError,
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
        customer_email="test@example.com",
    ):
        self.hosted_page = MockChargeBeeHostedPage(
            subscription_id=subscription_id,
            plan_id=plan_id,
            created_at=created_at,
            customer_id=customer_id,
            customer_email=customer_email,
        )


class MockChargeBeeHostedPage:
    def __init__(
        self,
        subscription_id,
        plan_id,
        created_at,
        customer_id,
        customer_email,
        hosted_page_id="some-id",
    ):
        self.id = hosted_page_id
        self.content = MockChargeBeeHostedPageContent(
            subscription_id=subscription_id,
            plan_id=plan_id,
            created_at=created_at,
            customer_id=customer_id,
            customer_email=customer_email,
        )


class MockChargeBeeHostedPageContent:
    def __init__(
        self, subscription_id, plan_id, created_at, customer_id, customer_email
    ):
        self.subscription = MockChargeBeeSubscription(
            subscription_id=subscription_id, plan_id=plan_id, created_at=created_at
        )
        self.customer = MockChargeBeeCustomer(customer_id, customer_email)


class MockChargeBeeAddOn:
    def __init__(self, addon_id: str, quantity: int):
        self.id = addon_id
        self.quantity = quantity


class MockChargeBeeSubscriptionResponse:
    def __init__(
        self,
        subscription_id: str = "subscription-id",
        plan_id: str = "plan-id",
        created_at: datetime = None,
        customer_id: str = "customer-id",
        customer_email: str = "test@example.com",
        addons: list[MockChargeBeeAddOn] = None,
    ):
        self.subscription = MockChargeBeeSubscription(
            subscription_id, plan_id, created_at or datetime.now(), addons
        )
        self.customer = MockChargeBeeCustomer(customer_id, customer_email)


class MockChargeBeeSubscription:
    def __init__(
        self,
        subscription_id: str,
        plan_id: str,
        created_at: datetime,
        addons: list[MockChargeBeeAddOn] = None,
    ):
        self.id = subscription_id
        self.plan_id = plan_id
        self.created_at = datetime.timestamp(created_at)
        self.addons = addons or []


class MockChargeBeeCustomer:
    def __init__(self, customer_id, customer_email):
        self.id = customer_id
        self.email = customer_email


class MockChargeBeePortalSessionResponse:
    def __init__(self, access_url="https://test.portal.url"):
        self.portal_session = MockChargeBeePortalSession(access_url)


class MockChargeBeePortalSession:
    def __init__(self, access_url):
        self.access_url = access_url


def test_chargebee_get_max_seats_for_plan_returns_max_seats_for_plan() -> None:
    # Given
    monkeypatch = MonkeyPatch()
    mock_cb = mock.MagicMock()

    monkeypatch.setattr("organisations.chargebee.chargebee.chargebee", mock_cb)

    meta_data = {"seats": 3, "api_calls": 50000}

    # When
    max_seats = get_max_seats_for_plan(meta_data)

    # Then
    assert max_seats == meta_data["seats"]


def test_chargebee_get_max_api_calls_for_plan_returns_max_api_calls_for_plan() -> None:
    # Given
    monkeypatch = MonkeyPatch()
    mock_cb = mock.MagicMock()

    monkeypatch.setattr("organisations.chargebee.chargebee.chargebee", mock_cb)
    meta_data = {"seats": 3, "api_calls": 50000}

    # When
    max_api_calls = get_max_api_calls_for_plan(meta_data)

    # Then
    assert max_api_calls == meta_data["api_calls"]


def test_chargebee_get_plan_meta_data_returns_correct_metadata() -> None:
    # Given
    plan_id = "startup"
    expected_max_seats = 3
    expected_max_api_calls = 50
    monkeypatch = MonkeyPatch()
    mock_cb = mock.MagicMock()

    monkeypatch.setattr("organisations.chargebee.chargebee.chargebee", mock_cb)

    mock_cb.Plan.retrieve.return_value = MockChargeBeePlanResponse(
        expected_max_seats, expected_max_api_calls
    )

    # When
    plan_meta_data = get_plan_meta_data(plan_id)

    # Then
    assert plan_meta_data == {
        "api_calls": expected_max_api_calls,
        "seats": expected_max_seats,
    }
    mock_cb.Plan.retrieve.assert_called_with(plan_id)


def test_chargebee_get_subscription_data_from_hosted_page_returns_expected_values() -> (
    None
):
    # Given
    subscription_id = "abc123"
    plan_id = "startup"
    expected_max_seats = 3
    created_at = datetime.now(tz=UTC)
    customer_id = "customer-id"
    monkeypatch = MonkeyPatch()
    mock_cb = mock.MagicMock()

    monkeypatch.setattr("organisations.chargebee.chargebee.chargebee", mock_cb)

    mock_cb.HostedPage.retrieve.return_value = MockChargeBeeHostedPageResponse(
        subscription_id=subscription_id,
        plan_id=plan_id,
        created_at=created_at,
        customer_id=customer_id,
    )
    mock_cb.Plan.retrieve.return_value = MockChargeBeePlanResponse(expected_max_seats)

    # When
    subscription_data = get_subscription_data_from_hosted_page("hosted_page_id")

    # Then
    assert subscription_data["subscription_id"] == subscription_id
    assert subscription_data["plan"] == plan_id
    assert subscription_data["max_seats"] == expected_max_seats
    assert subscription_data["subscription_date"] == created_at
    assert subscription_data["customer_id"] == customer_id


def test_get_chargebee_portal_url() -> None:
    # Given
    access_url = "https://test.url.com"
    monkeypatch = MonkeyPatch()
    mock_cb = mock.MagicMock()

    monkeypatch.setattr("organisations.chargebee.chargebee.chargebee", mock_cb)

    mock_cb.PortalSession.create.return_value = MockChargeBeePortalSessionResponse(
        access_url
    )

    # When
    portal_url = get_portal_url("some-customer-id", "https://redirect.url.com")

    # Then
    assert portal_url == access_url


def test_chargebee_get_customer_id_from_subscription() -> None:
    # Given
    expected_customer_id = "customer-id"
    monkeypatch = MonkeyPatch()
    mock_cb = mock.MagicMock()

    monkeypatch.setattr("organisations.chargebee.chargebee.chargebee", mock_cb)
    mock_cb.Subscription.retrieve.return_value = MockChargeBeeSubscriptionResponse(
        customer_id=expected_customer_id
    )

    # When
    customer_id = get_customer_id_from_subscription_id("subscription-id")

    # Then
    assert customer_id == expected_customer_id


def test_chargebee_get_hosted_page_url_for_subscription_upgrade() -> None:
    # Given
    subscription_id = "test-id"
    plan_id = "plan-id"
    url = "https://some.url.com/some/page/"
    monkeypatch = MonkeyPatch()
    mock_cb = mock.MagicMock()

    monkeypatch.setattr("organisations.chargebee.chargebee.chargebee", mock_cb)
    mock_cb.HostedPage.checkout_existing.return_value = mock.MagicMock(
        hosted_page=mock.MagicMock(url=url)
    )

    # When
    response = get_hosted_page_url_for_subscription_upgrade(subscription_id, plan_id)

    # Then
    assert response == url
    mock_cb.HostedPage.checkout_existing.assert_called_once_with(
        {"subscription": {"id": subscription_id, "plan_id": plan_id}}
    )


def test_extract_subscription_metadata(
    mock_subscription_response_with_addons: MockChargeBeeSubscriptionResponse,
    chargebee_object_metadata: ChargebeeObjMetadata,
) -> None:
    # Given
    status = "status"
    plan_id = "plan-id"
    addon_id = "addon-id"
    subscription_id = "subscription-id"
    customer_email = "test@example.com"

    subscription = {
        "status": status,
        "id": subscription_id,
        "plan_id": plan_id,
        "addons": [
            {
                "id": addon_id,
                "quantity": 2,
                "unit_price": 0,
                "amount": 0,
            }
        ],
    }

    # When
    subscription_metadata = extract_subscription_metadata(
        subscription,
        customer_email,
    )

    # Then
    # Note that we multiply by 3 since the plan and the addons carry the same limits,
    # so we have 1 plan + 2 addons.
    assert subscription_metadata.seats == chargebee_object_metadata.seats * 3
    assert subscription_metadata.api_calls == chargebee_object_metadata.api_calls * 3
    assert subscription_metadata.projects == chargebee_object_metadata.projects * 3
    assert subscription_metadata.chargebee_email == customer_email


def test_extract_subscription_metadata_when_addon_list_is_empty(
    mock_subscription_response_with_addons: MockChargeBeeSubscriptionResponse,
    chargebee_object_metadata: ChargebeeObjMetadata,
) -> None:
    # Given
    status = "status"
    plan_id = "plan-id"
    subscription_id = "subscription-id"
    customer_email = "test@example.com"

    subscription = {
        "status": status,
        "id": subscription_id,
        "plan_id": plan_id,
        "addons": [],
    }

    # When
    subscription_metadata = extract_subscription_metadata(
        subscription,
        customer_email,
    )

    # Then
    assert subscription_metadata.seats == chargebee_object_metadata.seats
    assert subscription_metadata.api_calls == chargebee_object_metadata.api_calls
    assert subscription_metadata.projects == chargebee_object_metadata.projects
    assert subscription_metadata.chargebee_email == customer_email


def test_get_subscription_metadata_from_id(
    mock_subscription_response_with_addons: MockChargeBeeSubscriptionResponse,
    chargebee_object_metadata: ChargebeeObjMetadata,
) -> None:
    # Given
    customer_email = "test@example.com"
    subscription_id = mock_subscription_response_with_addons.subscription.id

    # When
    subscription_metadata = get_subscription_metadata_from_id(subscription_id)

    # Then
    # Values here are multiplied by 2 because the both the plan and the addon included in
    # the mock_subscription_response_with_addons fixture contain the same values.
    assert subscription_metadata.seats == chargebee_object_metadata.seats * 2
    assert subscription_metadata.api_calls == chargebee_object_metadata.api_calls * 2
    assert subscription_metadata.projects == chargebee_object_metadata.projects * 2
    assert subscription_metadata.chargebee_email == customer_email


def test_cancel_subscription(mocker) -> None:
    # Given
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")
    subscription_id = "sub-id"

    # When
    cancel_subscription(subscription_id)

    # Then
    mocked_chargebee.Subscription.cancel.assert_called_once_with(
        subscription_id, {"end_of_term": True}
    )


def test_cancel_subscription_throws_cannot_cancel_error_if_api_error(
    mocker, caplog
) -> None:
    # Given
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")
    subscription_id = "sub-id"

    # Chargebee's APIError requires additional arguments to instantiate it so instead
    # we mock it with our own exception here to test that it is caught correctly
    class MockException(Exception):
        pass

    mocker.patch("organisations.chargebee.chargebee.ChargebeeAPIError", MockException)

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


def test_get_subscription_metadata_from_id_returns_null_if_chargebee_error(
    mocker, chargebee_object_metadata
) -> None:
    # Given
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")
    mocked_chargebee.Subscription.retrieve.side_effect = APIError(
        http_code=200, json_obj=mocker.MagicMock()
    )

    subscription_id = "foo"  # arbitrary subscription id

    # When
    subscription_metadata = get_subscription_metadata_from_id(subscription_id)

    # Then
    assert subscription_metadata is None


@pytest.mark.parametrize(
    "subscription_id",
    [None, "", " "],
)
def test_get_subscription_metadata_from_id_returns_none_for_invalid_subscription_id(
    mocker, chargebee_object_metadata, subscription_id
) -> None:
    # Given
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")

    # When
    subscription_metadata = get_subscription_metadata_from_id(subscription_id)

    # Then
    mocked_chargebee.Subscription.retrieve.assert_not_called()
    assert subscription_metadata is None


def test_get_subscription_metadata_from_id_returns_valid_metadata_if_addons_is_none(
    mock_subscription_response: MockChargeBeeSubscriptionResponse,
    chargebee_object_metadata: ChargebeeObjMetadata,
) -> None:
    # Given
    mock_subscription_response.addons = None
    subscription_id = mock_subscription_response.subscription.id

    # When
    subscription_metadata = get_subscription_metadata_from_id(subscription_id)

    # Then
    assert subscription_metadata.seats == chargebee_object_metadata.seats
    assert subscription_metadata.api_calls == chargebee_object_metadata.api_calls
    assert subscription_metadata.projects == chargebee_object_metadata.projects


def test_add_single_seat_with_existing_addon(mocker) -> None:
    # Given
    plan_id = "plan-id"
    addon_id = ADDITIONAL_SEAT_ADDON_ID
    subscription_id = "subscription-id"
    addon_quantity = 1

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

    # When
    add_single_seat(subscription_id)

    # Then
    mocked_chargebee.Subscription.update.assert_called_once_with(
        subscription_id,
        {
            "addons": [
                {"id": ADDITIONAL_SEAT_ADDON_ID, "quantity": addon_quantity + 1}
            ],
            "prorate": True,
            "invoice_immediately": False,
        },
    )


def test_add_single_seat_without_existing_addon(mocker) -> None:
    # Given
    subscription_id = "subscription-id"

    # Let's create a (mocked) subscription object
    mocked_subscription = mocker.MagicMock(
        id=subscription_id,
        plan_id="plan_id",
        addons=[],
    )
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")

    # tie that subscription object to the mocked chargebee object
    mocked_chargebee.Subscription.retrieve.return_value.subscription = (
        mocked_subscription
    )

    # When
    add_single_seat(subscription_id)

    # Then
    mocked_chargebee.Subscription.update.assert_called_once_with(
        subscription_id,
        {
            "addons": [{"id": ADDITIONAL_SEAT_ADDON_ID, "quantity": 1}],
            "prorate": True,
            "invoice_immediately": False,
        },
    )


def test_add_single_seat_throws_upgrade_seats_error_error_if_api_error(
    mocker, caplog
) -> None:
    # Given
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")

    # Typical non-payment related error from Chargebee.
    chargebee_response_data = {
        "message": "82sa2Sqa5 not found",
        "type": "invalid_request",
        "api_error_code": "resource_not_found",
        "param": "item_id",
        "error_code": "DeprecatedField",
    }
    mocked_chargebee.Subscription.update.side_effect = APIError(
        http_code=404, json_obj=chargebee_response_data
    )

    # Let's create a (mocked) subscription object
    subscription_id = "sub-id"
    mocked_subscription = mocker.MagicMock(
        id=subscription_id,
        plan_id="plan-id",
        addons=[],
    )

    # tie that subscription object to the mocked chargebee object
    mocked_chargebee.Subscription.retrieve.return_value.subscription = (
        mocked_subscription
    )

    # When
    with pytest.raises(UpgradeSeatsError):
        add_single_seat(subscription_id)

    # Then
    mocked_chargebee.Subscription.update.assert_called_once_with(
        subscription_id,
        {
            "addons": [{"id": ADDITIONAL_SEAT_ADDON_ID, "quantity": 1}],
            "prorate": True,
            "invoice_immediately": False,
        },
    )
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "ERROR"
    assert (
        caplog.records[0].message
        == "Failed to add additional seat to CB subscription for subscription id: %s"
        % subscription_id
    )

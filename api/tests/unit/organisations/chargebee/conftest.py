import typing

import pytest
from pytest_mock import MockerFixture

from organisations.chargebee.metadata import ChargebeeObjMetadata
from tests.unit.organisations.chargebee.test_unit_chargebee_chargebee import (
    MockChargeBeeAddOn,
    MockChargeBeeSubscriptionResponse,
)

ChargebeeCacheMocker = typing.Callable[
    [
        typing.Optional[dict[str, ChargebeeObjMetadata]],
        typing.Optional[dict[str, ChargebeeObjMetadata]],
    ],
    None,
]


@pytest.fixture
def chargebee_object_metadata():
    return ChargebeeObjMetadata(seats=10, api_calls=100, projects=10)


@pytest.fixture
def mock_subscription_response(
    mocker: MockerFixture,
    chargebee_object_metadata: ChargebeeObjMetadata,
    chargebee_cache_mocker: ChargebeeCacheMocker,
) -> MockChargeBeeSubscriptionResponse:
    # Given
    plan_id = "plan-id"
    subscription_id = "subscription-id"
    customer_email = "test@example.com"

    # Let's create a (mocked) subscription object
    mock_subscription_response = MockChargeBeeSubscriptionResponse(
        subscription_id=subscription_id,
        plan_id=plan_id,
        customer_email=customer_email,
        addons=None,
    )
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")

    # tie that subscription object to the mocked chargebee object
    mocked_chargebee.Subscription.retrieve.return_value = mock_subscription_response

    # now, let's mock chargebee cache object
    chargebee_cache_mocker({plan_id: chargebee_object_metadata}, None)

    return mock_subscription_response


@pytest.fixture
def mock_subscription_response_with_addons(
    mocker: MockerFixture,
    chargebee_object_metadata: ChargebeeObjMetadata,
    chargebee_cache_mocker: ChargebeeCacheMocker,
) -> MockChargeBeeSubscriptionResponse:
    # Given
    plan_id = "plan-id"
    addon_id = "addon-id"
    subscription_id = "subscription-id"
    customer_email = "test@example.com"

    # Let's create a (mocked) subscription object
    mock_subscription_response = MockChargeBeeSubscriptionResponse(
        subscription_id=subscription_id,
        plan_id=plan_id,
        customer_email=customer_email,
        addons=[MockChargeBeeAddOn(addon_id=addon_id, quantity=1)],
    )
    mocked_chargebee = mocker.patch("organisations.chargebee.chargebee.chargebee")

    # tie that subscription object to the mocked chargebee object
    mocked_chargebee.Subscription.retrieve.return_value = mock_subscription_response

    # now, let's mock chargebee cache object
    chargebee_cache_mocker(
        {plan_id: chargebee_object_metadata}, {addon_id: chargebee_object_metadata}
    )

    return mock_subscription_response


@pytest.fixture()
def chargebee_cache_mocker(
    mocker: MockerFixture,
) -> ChargebeeCacheMocker:
    def mock_chargebee_cache(
        plans_data: dict[str, ChargebeeObjMetadata] = None,
        addons_data: dict[str, ChargebeeObjMetadata] = None,
    ) -> None:
        mocked_chargebee_cache = mocker.patch(
            "organisations.chargebee.chargebee.ChargebeeCache", autospec=True
        )
        mocked_chargebee_cache.return_value.plans = plans_data or {}
        mocked_chargebee_cache.return_value.addons = addons_data or {}

    return mock_chargebee_cache

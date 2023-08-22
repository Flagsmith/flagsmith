import pytest
from pytest_mock import MockerFixture
from tests.unit.organisations.chargebee.test_unit_chargebee_chargebee import (
    MockChargeBeeAddOn,
    MockChargeBeeSubscriptionResponse,
)

from organisations.chargebee.metadata import ChargebeeObjMetadata


@pytest.fixture
def chargebee_object_metadata():
    return ChargebeeObjMetadata(seats=10, api_calls=100, projects=10)


@pytest.fixture
def mock_subscription_response(
    mocker: MockerFixture,
    chargebee_object_metadata: ChargebeeObjMetadata,
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
    mocked_chargebee_cache = mocker.patch(
        "organisations.chargebee.chargebee.ChargebeeCache", autospec=True
    )
    mocked_chargebee_cache.return_value.plans = {plan_id: chargebee_object_metadata}
    mocked_chargebee_cache.return_value.addons = {addon_id: chargebee_object_metadata}

    return mock_subscription_response

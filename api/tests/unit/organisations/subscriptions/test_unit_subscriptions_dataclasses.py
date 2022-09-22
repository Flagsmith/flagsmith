import pytest

from organisations.subscriptions.constants import CHARGEBEE, XERO
from organisations.subscriptions.dataclasses import BaseSubscriptionMetadata


def test_base_subscription_metadata_add_raises_error_if_not_matching_payment_source():
    # Given
    cb_metadata = BaseSubscriptionMetadata(
        seats=1, api_calls=50000, payment_source=CHARGEBEE
    )
    xero_metadata = BaseSubscriptionMetadata(
        seats=1, api_calls=50000, payment_source=XERO
    )

    # When
    with pytest.raises(TypeError):
        cb_metadata + xero_metadata

    # Then
    # exception was raised


@pytest.mark.parametrize(
    "add_to, add, expected_result",
    (
        (
            BaseSubscriptionMetadata(
                seats=1, api_calls=50000, payment_source=CHARGEBEE
            ),
            BaseSubscriptionMetadata(
                seats=1, api_calls=50000, payment_source=CHARGEBEE
            ),
            BaseSubscriptionMetadata(
                seats=2, api_calls=100000, projects=None, payment_source=CHARGEBEE
            ),
        ),
        (
            BaseSubscriptionMetadata(
                seats=1, api_calls=50000, projects=1, payment_source=CHARGEBEE
            ),
            BaseSubscriptionMetadata(
                seats=1, api_calls=50000, projects=1, payment_source=CHARGEBEE
            ),
            BaseSubscriptionMetadata(
                seats=2, api_calls=100000, projects=2, payment_source=CHARGEBEE
            ),
        ),
        (
            BaseSubscriptionMetadata(
                seats=1, api_calls=50000, projects=1, payment_source=CHARGEBEE
            ),
            BaseSubscriptionMetadata(
                seats=1, api_calls=50000, payment_source=CHARGEBEE
            ),
            BaseSubscriptionMetadata(
                seats=2, api_calls=100000, projects=1, payment_source=CHARGEBEE
            ),
        ),
        (
            BaseSubscriptionMetadata(
                seats=1, api_calls=50000, payment_source=CHARGEBEE
            ),
            BaseSubscriptionMetadata(
                seats=1, api_calls=50000, projects=1, payment_source=CHARGEBEE
            ),
            BaseSubscriptionMetadata(
                seats=2, api_calls=100000, projects=1, payment_source=CHARGEBEE
            ),
        ),
    ),
)
def test_base_subscription_metadata_add(add_to, add, expected_result):
    assert add_to + add == expected_result

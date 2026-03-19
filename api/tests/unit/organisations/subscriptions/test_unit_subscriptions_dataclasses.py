import pytest

from organisations.subscriptions.metadata import BaseSubscriptionMetadata


class SourceASubscriptionMetadata(BaseSubscriptionMetadata):
    payment_source = "SOURCE_A"  # type: ignore[assignment]


class SourceBSubscriptionMetadata(BaseSubscriptionMetadata):
    payment_source = "SOURCE_B"  # type: ignore[assignment]


def test_base_subscription_metadata_add__different_payment_sources__raises_type_error():  # type: ignore[no-untyped-def]
    # Given
    source_a_metadata = SourceASubscriptionMetadata(seats=1, api_calls=50000)
    source_b_metadata = SourceBSubscriptionMetadata(seats=1, api_calls=50000)

    # When / Then
    with pytest.raises(TypeError):
        source_a_metadata + source_b_metadata


@pytest.mark.parametrize(
    "add_to, add, expected_result",
    (
        (
            SourceASubscriptionMetadata(seats=1, api_calls=50000),
            SourceASubscriptionMetadata(seats=1, api_calls=50000),
            SourceASubscriptionMetadata(seats=2, api_calls=100000, projects=None),
        ),
        (
            SourceASubscriptionMetadata(seats=1, api_calls=50000, projects=1),
            SourceASubscriptionMetadata(seats=1, api_calls=50000, projects=1),
            SourceASubscriptionMetadata(seats=2, api_calls=100000, projects=2),
        ),
        (
            SourceASubscriptionMetadata(seats=1, api_calls=50000, projects=1),
            SourceASubscriptionMetadata(seats=1, api_calls=50000),
            SourceASubscriptionMetadata(seats=2, api_calls=100000, projects=None),
        ),
        (
            SourceASubscriptionMetadata(seats=1, api_calls=50000),
            SourceASubscriptionMetadata(seats=1, api_calls=50000, projects=1),
            SourceASubscriptionMetadata(seats=2, api_calls=100000, projects=None),
        ),
        (
            SourceASubscriptionMetadata(seats=1, api_calls=50000),
            SourceASubscriptionMetadata(seats=1),
            SourceASubscriptionMetadata(seats=2, api_calls=50000),
        ),
    ),
)
def test_base_subscription_metadata_add__same_payment_source__returns_summed_metadata(  # type: ignore[no-untyped-def]
    add_to, add, expected_result
):
    # Given / When
    result = add_to + add

    # Then
    assert result == expected_result

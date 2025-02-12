import pytest

from environments.identities.models import Identity
from environments.models import Environment
from features.models import FeatureState
from integrations.segment.models import SegmentConfiguration
from integrations.segment.segment import SegmentWrapper


def test_segment_initialized_correctly():
    # Given
    api_key = "123key"
    base_url = "https://api.segment.io/"
    config = SegmentConfiguration(api_key=api_key, base_url=base_url)

    # When
    segment_wrapper = SegmentWrapper(config)

    # Then
    assert segment_wrapper.analytics.write_key == api_key
    assert segment_wrapper.analytics.host == base_url


@pytest.mark.django_db
def test_segment_when_generate_user_data_with_correct_values_then_success(
    environment: Environment,
    feature_state: FeatureState,
    feature_state_with_value: FeatureState,
    identity: Identity,
) -> None:
    # Given
    api_key = "123key"
    config = SegmentConfiguration(api_key=api_key)
    segment_wrapper = SegmentWrapper(config)

    # When
    user_data = segment_wrapper.generate_user_data(
        identity=identity, feature_states=[feature_state, feature_state_with_value]
    )

    # Then
    feature_properties = {
        feature_state.feature.name: feature_state.enabled,
        feature_state_with_value.feature.name: "foo",  # hardcoded here from the feature_state_with_value fixture
    }

    expected_user_data = {
        "user_id": identity.identifier,
        "traits": feature_properties,
    }

    assert expected_user_data == user_data

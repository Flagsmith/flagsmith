import pytest

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.segment.models import SegmentConfiguration
from integrations.segment.segment import SegmentWrapper
from organisations.models import Organisation
from projects.models import Project


def test_segment_initialized_correctly():
    # Given
    api_key = "123key"
    config = SegmentConfiguration(api_key=api_key)

    # When initialized
    segment_wrapper = SegmentWrapper(config)

    # Then
    assert segment_wrapper.analytics.write_key == api_key


@pytest.mark.django_db
def test_segment_when_generate_user_data_with_correct_values_then_success():
    # Given
    api_key = "123key"
    config = SegmentConfiguration(api_key=api_key)
    segment_wrapper = SegmentWrapper(config)
    identity = Identity(identifier="user123")

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    Environment.objects.create(name="Test Environment 1", project=project)
    feature = Feature.objects.create(name="Test Feature", project=project)
    feature_states = FeatureState.objects.filter(feature=feature)

    # When
    user_data = segment_wrapper.generate_user_data(
        identity=identity, feature_states=feature_states
    )

    # Then
    feature_properties = {}
    for feature_state in feature_states:
        value = feature_state.get_feature_state_value()
        feature_properties[feature_state.feature.name] = (
            value if (feature_state.enabled and value) else feature_state.enabled
        )

    expected_user_data = {
        "user_id": identity.identifier,
        "traits": feature_properties,
    }

    assert expected_user_data == user_data

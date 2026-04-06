import pytest
from pytest_mock import MockerFixture

from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.gitlab.constants import GitLabEventType
from integrations.gitlab.mappers import map_feature_states_to_dicts
from projects.models import Project


@pytest.mark.django_db
def test_map_feature_states_to_dicts__flag_updated__includes_env_data(
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        identity__isnull=True,
        feature_segment__isnull=True,
    )

    # When
    result = map_feature_states_to_dicts(
        [feature_state],
        GitLabEventType.FLAG_UPDATED.value,
    )

    # Then
    assert len(result) == 1
    assert result[0]["environment_name"] == environment.name
    assert "enabled" in result[0]
    assert "last_updated" in result[0]
    assert "environment_api_key" in result[0]


@pytest.mark.django_db
def test_map_feature_states_to_dicts__resource_removed__skips_env_data(
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        identity__isnull=True,
        feature_segment__isnull=True,
    )

    # When
    result = map_feature_states_to_dicts(
        [feature_state],
        GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
    )

    # Then
    assert len(result) == 1
    assert "environment_name" not in result[0]
    assert "enabled" not in result[0]


@pytest.mark.django_db
def test_map_feature_states_to_dicts__with_value__includes_feature_state_value(
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        identity__isnull=True,
        feature_segment__isnull=True,
    )
    feature_state.enabled = True
    feature_state.save()
    from features.models import FeatureStateValue

    fsv = FeatureStateValue.objects.get(feature_state=feature_state)
    fsv.string_value = "test_value"
    fsv.save()

    # When
    result = map_feature_states_to_dicts(
        [feature_state],
        GitLabEventType.FLAG_UPDATED.value,
    )

    # Then
    assert result[0]["feature_state_value"] == "test_value"


@pytest.mark.django_db
def test_map_feature_states_to_dicts__with_segment__includes_segment_name(
    project: Project,
    environment: Environment,
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given
    from unittest.mock import MagicMock

    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        identity__isnull=True,
        feature_segment__isnull=True,
    )
    mock_segment = MagicMock()
    mock_segment.segment.name = "beta_users"
    mocker.patch.object(
        type(feature_state),
        "feature_segment",
        new_callable=lambda: property(lambda self: mock_segment),
    )

    # When
    result = map_feature_states_to_dicts(
        [feature_state],
        GitLabEventType.FLAG_UPDATED.value,
    )

    # Then
    assert result[0]["segment_name"] == "beta_users"


@pytest.mark.django_db
def test_map_feature_states_to_dicts__empty_list__returns_empty() -> None:
    # Given
    # When
    result = map_feature_states_to_dicts([], GitLabEventType.FLAG_UPDATED.value)

    # Then
    assert result == []

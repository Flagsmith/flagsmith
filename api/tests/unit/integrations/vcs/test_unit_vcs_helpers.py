import pytest

from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.vcs.helpers import collect_feature_states_for_resource
from projects.models import Project


@pytest.mark.django_db
def test_collect_feature_states_for_resource__single_env__returns_states(
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    # When
    result = collect_feature_states_for_resource(
        feature_id=feature.id,
        project_id=project.id,
    )

    # Then
    assert len(result) >= 1
    assert all(isinstance(fs, FeatureState) for fs in result)
    assert all(fs.feature_id == feature.id for fs in result)


@pytest.mark.django_db
def test_collect_feature_states_for_resource__no_environments__returns_empty(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    Environment.objects.filter(project=project).delete()

    # When
    result = collect_feature_states_for_resource(
        feature_id=feature.id,
        project_id=project.id,
    )

    # Then
    assert result == []

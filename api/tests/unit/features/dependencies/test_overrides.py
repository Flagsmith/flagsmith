import pytest

from environments.identities.models import Identity
from environments.models import Environment
from evaluation.mappers import map_environment_to_evaluation_context
from features.dependencies.services import create_flag_dependency
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from projects.models import Project
from segments.models import Segment
from users.models import FFAdminUser
from util.mappers.engine import map_environment_to_engine


@pytest.fixture()
def prerequisite(project: Project) -> Feature:
    return Feature.objects.create(name="chicken", project=project)  # type: ignore[no-any-return]


@pytest.fixture()
def dependent(project: Project) -> Feature:
    return Feature.objects.create(  # type: ignore[no-any-return]
        name="egg", project=project, initial_value="wild egg"
    )


@pytest.fixture()
def dependency_segment(
    environment: Environment,
    dependent: Feature,
    prerequisite: Feature,
    admin_user: FFAdminUser,
) -> Segment:
    create_flag_dependency(
        environment=environment,
        feature=dependent,
        prerequisite_feature=prerequisite,
        author=admin_user,
    )
    return Segment.objects.get(feature=dependent, is_system_segment=True)  # type: ignore[no-any-return]


def get_default_feature_state(
    environment: Environment, feature: Feature
) -> FeatureState:
    return FeatureState.objects.get(  # type: ignore[no-any-return]
        environment=environment,
        feature=feature,
        feature_segment__isnull=True,
        identity__isnull=True,
    )


def test_map_environment_to_evaluation_context__dependency_override__serves_current_default_value(
    environment: Environment,
    dependent: Feature,
    dependency_segment: Segment,
) -> None:
    # Given
    default = get_default_feature_state(environment, dependent)
    default.feature_state_value.string_value = "farm egg"
    default.feature_state_value.save()

    # When
    context = map_environment_to_evaluation_context(
        environment=environment, segments=[dependency_segment]
    )

    # Then
    override = context["segments"][str(dependency_segment.pk)]["overrides"][0]
    assert override["value"] == "farm egg"
    assert override["enabled"] is False
    assert override["priority"] == 0


def test_map_environment_to_evaluation_context__dependency_override__serves_current_default_variants(
    environment: Environment,
    multivariate_feature: Feature,
    prerequisite: Feature,
    admin_user: FFAdminUser,
    identity: Identity,
) -> None:
    # Given
    create_flag_dependency(
        environment=environment,
        feature=multivariate_feature,
        prerequisite_feature=prerequisite,
        author=admin_user,
    )
    segment = Segment.objects.get(feature=multivariate_feature, is_system_segment=True)
    default = get_default_feature_state(environment, multivariate_feature)
    for mv_value, percentage in zip(
        default.multivariate_feature_state_values.order_by("id"), (100, 0, 0)
    ):
        MultivariateFeatureStateValue.objects.filter(pk=mv_value.pk).update(
            percentage_allocation=percentage
        )

    # When
    context = map_environment_to_evaluation_context(
        environment=environment, identity=identity, segments=[segment]
    )

    # Then
    override = context["segments"][str(segment.pk)]["overrides"][0]
    assert [variant["weight"] for variant in override["variants"]] == [100, 0, 0]


def test_map_environment_to_evaluation_context__system_segment_without_dependency__keeps_own_value(
    environment: Environment,
    project: Project,
    dependent: Feature,
) -> None:
    # Given
    segment = Segment.objects.create(
        name="rollout", project=project, feature=dependent, is_system_segment=True
    )
    override = FeatureState.objects.create(
        feature=dependent,
        environment=environment,
        feature_segment=FeatureSegment.objects.create(
            feature=dependent, segment=segment, environment=environment
        ),
    )
    override.feature_state_value.string_value = "rollout egg"
    override.feature_state_value.save()

    # When
    context = map_environment_to_evaluation_context(
        environment=environment, segments=[segment]
    )

    # Then
    override = context["segments"][str(segment.pk)]["overrides"][0]
    assert override["value"] == "rollout egg"


def test_map_environment_to_engine__dependency_override__serves_current_default_value(
    environment: Environment,
    dependent: Feature,
    dependency_segment: Segment,
) -> None:
    # Given
    default = get_default_feature_state(environment, dependent)
    default.feature_state_value.string_value = "farm egg"
    default.feature_state_value.save()

    # When
    result = map_environment_to_engine(environment)

    # Then
    segment_model = next(
        s for s in result.project.segments if s.id == dependency_segment.pk
    )
    (override,) = segment_model.feature_states
    assert override.feature_state_value == "farm egg"
    assert override.enabled is False
    assert override.feature_segment is not None
    assert override.feature_segment.priority == 0


def test_map_environment_to_engine__dependency_override__serves_current_default_variants(
    environment: Environment,
    multivariate_feature: Feature,
    prerequisite: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given
    create_flag_dependency(
        environment=environment,
        feature=multivariate_feature,
        prerequisite_feature=prerequisite,
        author=admin_user,
    )
    segment = Segment.objects.get(feature=multivariate_feature, is_system_segment=True)
    default = get_default_feature_state(environment, multivariate_feature)
    for mv_value, percentage in zip(
        default.multivariate_feature_state_values.order_by("id"), (100, 0, 0)
    ):
        MultivariateFeatureStateValue.objects.filter(pk=mv_value.pk).update(
            percentage_allocation=percentage
        )

    # When
    result = map_environment_to_engine(environment)

    # Then
    segment_model = next(s for s in result.project.segments if s.id == segment.pk)
    (override,) = segment_model.feature_states
    assert [
        mv_value.percentage_allocation
        for mv_value in override.multivariate_feature_state_values
    ] == [100, 0, 0]


def test_map_environment_to_engine__system_segment_without_dependency__keeps_own_value(
    environment: Environment,
    project: Project,
    dependent: Feature,
) -> None:
    # Given
    segment = Segment.objects.create(
        name="rollout", project=project, feature=dependent, is_system_segment=True
    )
    override = FeatureState.objects.create(
        feature=dependent,
        environment=environment,
        feature_segment=FeatureSegment.objects.create(
            feature=dependent, segment=segment, environment=environment
        ),
    )
    override.feature_state_value.string_value = "rollout egg"
    override.feature_state_value.save()

    # When
    result = map_environment_to_engine(environment)

    # Then
    segment_model = next(s for s in result.project.segments if s.id == segment.pk)
    assert segment_model.feature_states[0].feature_state_value == "rollout egg"

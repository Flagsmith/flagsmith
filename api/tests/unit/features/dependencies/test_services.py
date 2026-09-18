import pytest
from pytest_django import DjangoAssertNumQueries

from environments.models import Environment
from features.dependencies.services import validate_segment_flag_dependencies
from features.models import Feature, FeatureSegment, FeatureState
from projects.models import Project
from segments.models import Segment


@pytest.mark.parametrize("environment_count", [1, 2, 3])
def test_validate_segment_flag_dependencies__overrides_across_environments__queries_once_per_environment(
    django_assert_num_queries: DjangoAssertNumQueries,
    environment_count: int,
    project: Project,
    segment: Segment,
) -> None:
    # Given
    for environment_index in range(environment_count):
        environment = Environment.objects.create(
            name=f"environment{environment_index}", project=project
        )
        for feature_name in ["chicken", "egg", "hen"]:
            feature, _ = Feature.objects.get_or_create(
                name=feature_name, project=project
            )
            feature_segment = FeatureSegment.objects.create(
                feature=feature, segment=segment, environment=environment
            )
            FeatureState.objects.create(
                feature=feature,
                environment=environment,
                feature_segment=feature_segment,
            )

    # When / Then
    with django_assert_num_queries(1 + environment_count):
        validate_segment_flag_dependencies(segment)

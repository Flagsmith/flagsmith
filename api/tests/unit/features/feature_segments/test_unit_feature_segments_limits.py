from environments.models import Environment
from features.feature_segments.limits import exceeds_segment_override_limit
from features.models import Feature, FeatureSegment
from features.versioning.models import EnvironmentFeatureVersion
from projects.models import Project
from segments.models import Segment


def test_segment_override_limit_includes_all_feature_segments_states(
    project: Project,
    environment: Environment,
) -> None:
    # Given
    project.max_segment_overrides_allowed = 3
    project.save()

    features = [
        Feature.objects.create(name=f"feature_{i}", project=project) for i in range(5)
    ]
    segment = Segment.objects.create(name="shared_segment", project=project)

    for feature in features:
        FeatureSegment.objects.create(
            feature=feature, segment=segment, environment=environment
        )

    # When
    result = exceeds_segment_override_limit(environment=environment)

    # Then
    assert result is True


def test_segment_override_limit_is_triggered_with_distinct_segments_per_feature_states(
    project: Project,
    environment: Environment,
) -> None:
    # Given
    project.max_segment_overrides_allowed = 3
    project.save()

    features = [
        Feature.objects.create(name=f"feature_{i}", project=project) for i in range(5)
    ]
    segments = [
        Segment.objects.create(name=f"segment_{i}", project=project) for i in range(5)
    ]

    for feature, segment in zip(features, segments):
        FeatureSegment.objects.create(
            feature=feature, segment=segment, environment=environment
        )

    # When
    result = exceeds_segment_override_limit(environment=environment)

    # Then
    assert result is True


def test_segment_override_limit_v2_delete_count_uses_unique_segment_ids(
    project: Project,
    environment_v2_versioning: Environment,
) -> None:
    # Given
    project.max_segment_overrides_allowed = 5
    project.save()

    features = [
        Feature.objects.create(name=f"feature_{i}", project=project) for i in range(5)
    ]
    shared_segment = Segment.objects.create(name="shared_segment", project=project)
    new_segment = Segment.objects.create(name="new_segment", project=project)

    for feature in features:
        version = EnvironmentFeatureVersion.objects.get_or_create(
            environment=environment_v2_versioning,
            feature=feature,
        )[0]
        FeatureSegment.objects.create(
            feature=feature,
            segment=shared_segment,
            environment=environment_v2_versioning,
            environment_feature_version=version,
        )

    # When
    result = exceeds_segment_override_limit(
        environment=environment_v2_versioning,
        segment_ids_to_create_overrides=[new_segment.id],
        segment_ids_to_delete_overrides=[shared_segment.id],
    )

    # Then
    assert result is True


def test_segment_override_limit_does_not_exclude_invalid_overrides_being_deleted(
    feature: Feature,
    segment: Segment,
    another_segment: Segment,
    environment_v2_versioning: Environment,
    project: Project,
) -> None:
    # Given
    project.max_segment_overrides_allowed = 0
    project.save()

    # When
    result = exceeds_segment_override_limit(
        environment=environment_v2_versioning,
        segment_ids_to_create_overrides=[another_segment.id],
        segment_ids_to_delete_overrides=[segment.id],
    )

    # Then
    assert result is True

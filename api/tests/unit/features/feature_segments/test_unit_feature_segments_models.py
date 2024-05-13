from environments.models import Environment
from features.models import Feature, FeatureSegment
from projects.models import Project
from segments.models import Segment


def test_feature_segment_is_less_than_other_if_priority_lower(
    feature: Feature,
    environment: Environment,
    segment: Segment,
    project: Project,
) -> None:
    # Given
    feature_segment_1 = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment,
        priority=1,
    )

    another_segment = Segment.objects.create(name="Another segment", project=project)
    feature_segment_2 = FeatureSegment.objects.create(
        feature=feature,
        segment=another_segment,
        environment=environment,
        priority=2,
    )

    # When
    result = feature_segment_2 < feature_segment_1

    # Then
    assert result is True


def test_feature_segments_are_created_with_correct_priority(
    feature: Feature,
    environment: Environment,
    segment: Segment,
    project: Project,
) -> None:
    # Given - 5 feature segments

    # 2 with the same feature and environment but a different segment
    another_segment = Segment.objects.create(name="Another segment", project=project)
    feature_segment_1 = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment,
    )

    feature_segment_2 = FeatureSegment.objects.create(
        feature=feature,
        segment=another_segment,
        environment=environment,
    )

    # 1 with the same feature but a different environment
    another_environment = Environment.objects.create(
        name="Another environment", project=project
    )
    feature_segment_3 = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=another_environment,
    )

    # 1 with the same environment but a different feature
    another_feature = Feature.objects.create(name="Another feature", project=project)
    feature_segment_4 = FeatureSegment.objects.create(
        feature=another_feature, segment=segment, environment=environment
    )

    # 1 with a different feature and a different environment
    feature_segment_5 = FeatureSegment.objects.create(
        feature=another_feature,
        segment=segment,
        environment=another_environment,
    )

    # Then
    # the two with the same feature and environment are created with ascending priorities
    assert feature_segment_1.priority == 0
    assert feature_segment_2.priority == 1

    # the ones with different combinations of features and environments are all created with a priority of 0
    assert feature_segment_3.priority == 0
    assert feature_segment_4.priority == 0
    assert feature_segment_5.priority == 0


def test_clone_creates_a_new_object(
    feature: Feature,
    environment: Environment,
    segment: Segment,
    project: Project,
) -> None:
    # Given
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment,
        priority=1,
    )
    new_environment = Environment.objects.create(
        name="Test environment New", project=project
    )

    # When
    feature_segment_clone = feature_segment.clone(new_environment)

    # Then
    assert feature_segment_clone.id != feature_segment.id
    assert feature_segment_clone.priority == feature_segment.priority
    assert feature_segment_clone.environment.id == new_environment.id

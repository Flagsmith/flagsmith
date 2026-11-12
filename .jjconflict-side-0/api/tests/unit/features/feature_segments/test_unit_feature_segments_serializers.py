from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from environments.models import Environment
from features.feature_segments.serializers import (
    CustomCreateSegmentOverrideFeatureSegmentSerializer,
    FeatureSegmentChangePrioritiesSerializer,
)
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from segments.models import Segment
from users.models import FFAdminUser


def test_feature_segment_change_priorities_serializer__non_unique_version__validation_fails(  # type: ignore[no-untyped-def]  # noqa: E501
    feature: Feature,
    environment_v2_versioning: Environment,
    segment: Segment,
    admin_user: FFAdminUser,
):
    # Given
    version_1 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    v1_segment_override_feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment_v2_versioning
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=version_1,
        feature_segment=v1_segment_override_feature_segment,
    )

    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    v2_segment_override_feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment_v2_versioning
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=version_2,
        feature_segment=v2_segment_override_feature_segment,
    )

    data = [
        {"id": v1_segment_override_feature_segment.id, "priority": 10},
        {"id": v2_segment_override_feature_segment.id, "priority": 11},
    ]

    serializer = FeatureSegmentChangePrioritiesSerializer(
        data=data, many=True, context={"request": MagicMock(user=admin_user)}
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid is False
    assert serializer.errors


def test_feature_segment_serializer__new_segment_no_priority__sets_lowest_priority(
    feature: Feature,
    segment_featurestate: FeatureState,
    feature_segment: FeatureSegment,
    another_segment: Segment,
    environment: Environment,
) -> None:
    # Given
    serializer = CustomCreateSegmentOverrideFeatureSegmentSerializer(
        data={"segment": another_segment.id}
    )
    serializer.is_valid(raise_exception=True)

    # When
    new_feature_segment = serializer.save(feature=feature, environment=environment)

    # Then
    feature_segment.refresh_from_db()
    assert feature_segment.priority == 0
    assert new_feature_segment.priority == 1


def test_feature_segment_serializer__new_segment_priority_zero__sets_highest_priority(
    feature: Feature,
    segment_featurestate: FeatureState,
    feature_segment: FeatureSegment,
    another_segment: Segment,
    environment: Environment,
) -> None:
    # Given
    serializer = CustomCreateSegmentOverrideFeatureSegmentSerializer(
        data={"segment": another_segment.id, "priority": 0}
    )
    serializer.is_valid(raise_exception=True)

    # When
    new_feature_segment = serializer.save(feature=feature, environment=environment)

    # Then
    feature_segment.refresh_from_db()
    assert feature_segment.priority == 1
    assert new_feature_segment.priority == 0


def test_feature_segment_serializer__new_segment_with_priority__moves_others(
    feature: Feature,
    segment_featurestate: FeatureState,
    feature_segment: FeatureSegment,
    another_segment: Segment,
    environment: Environment,
) -> None:
    # Given
    feature_segment.to(1)

    serializer = CustomCreateSegmentOverrideFeatureSegmentSerializer(
        data={"segment": another_segment.id, "priority": 1}
    )
    serializer.is_valid(raise_exception=True)

    # When
    new_feature_segment = serializer.save(feature=feature, environment=environment)

    # Then
    feature_segment.refresh_from_db()
    assert feature_segment.priority == 2
    assert new_feature_segment.priority == 1


def test_feature_segment_serializer__existing_segment_no_priority__does_nothing(
    feature: Feature,
    segment_featurestate: FeatureState,
    feature_segment: FeatureSegment,
    another_segment: Segment,
    environment: Environment,
) -> None:
    # Given
    feature_segment_to_update = FeatureSegment.objects.create(
        environment=environment,
        feature=feature,
        segment=another_segment,
        priority=1,
    )

    serializer = CustomCreateSegmentOverrideFeatureSegmentSerializer(
        instance=feature_segment_to_update, data={"segment": another_segment.id}
    )
    serializer.is_valid(raise_exception=True)

    # When
    updated_feature_segment = serializer.save(feature=feature, environment=environment)

    # Then
    feature_segment.refresh_from_db()
    assert feature_segment.priority == 0
    assert updated_feature_segment.priority == 1


def test_feature_segment_serializer__existing_segment_priority_zero__sets_highest_priority(
    feature: Feature,
    segment_featurestate: FeatureState,
    feature_segment: FeatureSegment,
    another_segment: Segment,
    environment: Environment,
) -> None:
    # Given
    feature_segment_to_update = FeatureSegment.objects.create(
        environment=environment,
        feature=feature,
        segment=another_segment,
        priority=1,
    )

    serializer = CustomCreateSegmentOverrideFeatureSegmentSerializer(
        instance=feature_segment_to_update,
        data={"segment": another_segment.id, "priority": 0},
    )
    serializer.is_valid(raise_exception=True)

    # When
    updated_feature_segment = serializer.save(feature=feature, environment=environment)

    # Then
    feature_segment.refresh_from_db()
    assert feature_segment.priority == 1
    assert updated_feature_segment.priority == 0


def test_feature_segment_serializer__existing_segment_with_priority__moves_others(
    feature: Feature,
    segment_featurestate: FeatureState,
    feature_segment: FeatureSegment,
    another_segment: Segment,
    environment: Environment,
) -> None:
    # Given
    feature_segment.to(1)

    feature_segment_to_update = FeatureSegment.objects.create(
        environment=environment,
        feature=feature,
        segment=another_segment,
    )

    serializer = CustomCreateSegmentOverrideFeatureSegmentSerializer(
        instance=feature_segment_to_update,
        data={"segment": another_segment.id, "priority": 1},
    )
    serializer.is_valid(raise_exception=True)

    # When
    updated_feature_segment = serializer.save(feature=feature, environment=environment)

    # Then
    feature_segment.refresh_from_db()
    assert feature_segment.priority == 2
    assert updated_feature_segment.priority == 1


def test_feature_segment_serializer__new_segment_create_error__does_nothing(
    feature: Feature,
    segment_featurestate: FeatureState,
    feature_segment: FeatureSegment,
    another_segment: Segment,
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    feature_segment.to(1)
    serializer = CustomCreateSegmentOverrideFeatureSegmentSerializer(
        data={"segment": another_segment.id, "priority": 1},
    )
    serializer.is_valid(raise_exception=True)

    class MockException(Exception):
        pass

    mocker.patch(
        "features.feature_segments.serializers.CustomCreateSegmentOverrideFeatureSegmentSerializer.create",
        side_effect=MockException,
    )

    # When
    with pytest.raises(MockException):
        serializer.save(feature=feature, environment=environment)

    # Then
    feature_segment.refresh_from_db()
    assert feature_segment.priority == 1

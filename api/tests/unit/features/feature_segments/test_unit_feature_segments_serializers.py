from unittest.mock import MagicMock

from environments.models import Environment
from features.feature_segments.serializers import (
    FeatureSegmentChangePrioritiesSerializer,
)
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from segments.models import Segment
from users.models import FFAdminUser


def test_feature_segment_change_priorities_serializer_validate_fails_if_non_unique_version(
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

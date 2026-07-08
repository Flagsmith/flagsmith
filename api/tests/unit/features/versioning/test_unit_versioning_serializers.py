from environments.models import Environment
from features.models import Feature
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.serializers import (
    CustomEnvironmentFeatureVersionFeatureStateSerializer,
)
from segments.models import Segment


def test_get_inherited_mv_hashing_salt__no_feature_segment__returns_none(
    environment_v2_versioning: Environment,
    feature: Feature,
) -> None:
    # Given
    version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )
    serializer = CustomEnvironmentFeatureVersionFeatureStateSerializer()

    # When
    inherited_salt = serializer._get_inherited_mv_hashing_salt(
        {"environment_feature_version": version}
    )

    # Then
    assert inherited_salt is None


def test_get_inherited_mv_hashing_salt__no_previous_version__returns_none(
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
) -> None:
    # Given
    initial_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )
    serializer = CustomEnvironmentFeatureVersionFeatureStateSerializer()

    # When
    inherited_salt = serializer._get_inherited_mv_hashing_salt(
        {
            "environment_feature_version": initial_version,
            "feature_segment": {"segment": segment},
        }
    )

    # Then
    assert inherited_salt is None

import typing

from environments.models import Environment
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import create_initial_feature_versions

if typing.TYPE_CHECKING:
    from features.models import Feature


def test_create_initial_feature_versions_does_nothing_if_environment_not_using_v2_versioning(
    environment: "Environment", feature: "Feature"
) -> None:
    # When
    create_initial_feature_versions(environment.id)

    # Then
    assert not EnvironmentFeatureVersion.objects.filter(
        environment=environment, feature=feature
    ).exists()

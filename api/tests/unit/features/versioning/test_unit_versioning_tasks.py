import typing

from environments.models import Environment
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import enable_v2_versioning

if typing.TYPE_CHECKING:
    from features.models import Feature


def test_enable_v2_versioning_does_nothing_if_environment_not_using_v2_versioning(
    environment: "Environment", feature: "Feature"
) -> None:
    # When
    enable_v2_versioning(environment.id)

    # Then
    assert not EnvironmentFeatureVersion.objects.filter(
        environment=environment, feature=feature
    ).exists()

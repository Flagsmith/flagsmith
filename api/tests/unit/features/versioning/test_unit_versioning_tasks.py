from environments.models import Environment
from features.models import Feature
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import enable_v2_versioning


def test_enable_v2_versioning(
    environment: Environment, feature: Feature, multivariate_feature: Feature
) -> None:
    # When
    enable_v2_versioning(environment.id)

    # Then
    assert EnvironmentFeatureVersion.objects.filter(
        environment=environment, feature=feature
    ).exists()
    assert EnvironmentFeatureVersion.objects.filter(
        environment=environment, feature=multivariate_feature
    ).exists()

    environment.refresh_from_db()
    assert environment.use_v2_feature_versioning is True

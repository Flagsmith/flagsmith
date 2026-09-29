from environments.models import Environment
from features.exceptions import FeatureNotFoundError
from features.models import Feature


def get_feature(environment: Environment, feature_id: int) -> Feature:
    """Fetch a feature of the environment's project, or refuse with a 404."""
    try:
        return Feature.objects.get(  # type: ignore[no-any-return]
            id=feature_id, project_id=environment.project_id
        )
    except Feature.DoesNotExist:
        raise FeatureNotFoundError(feature_id) from None

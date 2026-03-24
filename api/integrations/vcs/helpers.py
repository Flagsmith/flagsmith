from django.db.models import Q

from environments.models import Environment
from features.models import FeatureState


def collect_feature_states_for_resource(
    feature_id: int, project_id: int
) -> list[FeatureState]:
    """Collect live feature states across all environments for a feature.

    Used by both GitHub and GitLab integrations when a feature is linked
    to an external resource.
    """
    feature_states: list[FeatureState] = []
    environments = Environment.objects.filter(project_id=project_id)

    for environment in environments:
        q = Q(feature_id=feature_id, identity__isnull=True)
        feature_states.extend(
            FeatureState.objects.get_live_feature_states(
                environment=environment, additional_filters=q
            )
        )

    return feature_states

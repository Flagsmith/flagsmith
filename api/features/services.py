from django.db import transaction

from environments.models import Environment
from features.dependencies.services import (
    get_prerequisite_feature_names_by_environment,
    report_flag_dependencies,
    validate_feature_is_not_prerequisite,
)
from features.dependencies.types import FeatureName
from features.exceptions import FeatureNotFoundError
from features.models import Feature
from features.tasks import trigger_feature_state_change_webhooks
from webhooks.webhooks import WebhookEventType


def get_feature(environment: Environment, feature_id: int) -> Feature:
    """Fetch a feature of the environment's project, or refuse with a 404."""
    try:
        return Feature.objects.get(  # type: ignore[no-any-return]
            id=feature_id, project_id=environment.project_id
        )
    except Feature.DoesNotExist:
        raise FeatureNotFoundError(feature_id) from None


def delete_feature(feature: Feature) -> None:
    """Delete the feature from every environment, or refuse with a 400."""
    with transaction.atomic():
        validate_feature_is_not_prerequisite(feature)
        _trigger_environment_defaults_deleted_webhooks(feature)
        prerequisite_feature_names_by_environment = (
            get_prerequisite_feature_names_by_environment(feature)
        )
        feature.delete()
    _report_prerequisites_lost(feature, prerequisite_feature_names_by_environment)


def _report_prerequisites_lost(
    feature: Feature,
    prerequisite_feature_names_by_environment: dict[Environment, set[FeatureName]],
) -> None:
    for environment, names in prerequisite_feature_names_by_environment.items():
        report_flag_dependencies(
            environment=environment, feature=feature, created=[], deleted=names
        )


def _trigger_environment_defaults_deleted_webhooks(feature: Feature) -> None:
    for feature_state in feature.feature_states.filter(
        identity=None, feature_segment=None
    ):
        trigger_feature_state_change_webhooks(
            feature_state, WebhookEventType.FLAG_DELETED
        )

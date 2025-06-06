import logging

from task_processor.decorators import register_task_handler

from environments.models import Environment

from .change_tracking import post_change_tracking_update_to_sentry

logger = logging.getLogger(__name__)


@register_task_handler()
def send_sentry_change_tracking_webhook_update(feature_state_id: int) -> None:
    from features.models import FeatureState

    feature_state = FeatureState.objects.get(pk=feature_state_id)

    try:
        sentry_configuration = (
            feature_state.environment.sentry_change_tracking_configuration
        )
    except Environment.sentry_change_tracking_configuration.RelatedObjectDoesNotExist:
        return

    post_change_tracking_update_to_sentry(feature_state, sentry_configuration)

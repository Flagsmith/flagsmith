import logging
from typing import Any

from task_processor.decorators import (
    register_task_handler,
)

from environments.models import Webhook
from features.models import Feature, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from webhooks.constants import WEBHOOK_DATETIME_FORMAT
from webhooks.tasks import (
    call_environment_webhooks,
    call_organisation_webhooks,
)
from webhooks.webhooks import WebhookEventType

from .models import HistoricalFeatureState  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


def trigger_feature_state_change_webhooks(  # type: ignore[no-untyped-def]
    instance: FeatureState, event_type: WebhookEventType = WebhookEventType.FLAG_UPDATED
):
    assert event_type in [WebhookEventType.FLAG_UPDATED, WebhookEventType.FLAG_DELETED]

    history_instance = instance.history.first()
    timestamp = (
        history_instance.history_date.strftime(WEBHOOK_DATETIME_FORMAT)
        if history_instance and history_instance.history_date
        else ""
    )
    changed_by = (
        history_instance.history_user.email
        if history_instance and history_instance.history_user
        else (
            history_instance.master_api_key.name
            if history_instance and history_instance.master_api_key
            else ""
        )
    )
    new_state = (
        None
        if event_type == WebhookEventType.FLAG_DELETED
        else _get_feature_state_webhook_data(instance)
    )
    data = {"new_state": new_state, "changed_by": changed_by, "timestamp": timestamp}
    previous_state = _get_previous_state(instance, history_instance, event_type)

    if previous_state:
        data.update(previous_state=previous_state)

    call_environment_webhooks.delay(
        args=(instance.environment.id, data, event_type.value)  # type: ignore[union-attr]
    )

    call_organisation_webhooks.delay(
        args=(
            instance.environment.project.organisation.id,  # type: ignore[union-attr]
            data,
            event_type.value,
        )
    )


def _get_previous_state(
    instance: FeatureState,
    history_instance: HistoricalFeatureState,
    event_type: WebhookEventType,
) -> dict:  # type: ignore[type-arg]
    if event_type == WebhookEventType.FLAG_DELETED:
        return _get_feature_state_webhook_data(instance)
    if history_instance and history_instance.prev_record:
        return _get_feature_state_webhook_data(
            history_instance.prev_record.instance, previous=True
        )
    return None  # type: ignore[return-value]


def _get_feature_state_webhook_data(
    feature_state: FeatureState,
    previous: bool = False,
) -> dict[str, Any]:
    if previous:
        value = feature_state.previous_feature_state_value
        mv_values = _get_previous_multivariate_values(feature_state)
    else:
        value = feature_state.get_feature_state_value()
        mv_values = list(feature_state.multivariate_feature_state_values.all())

    assert feature_state.environment is not None
    return Webhook.generate_webhook_feature_state_data(
        feature_state.feature,
        environment=feature_state.environment,
        enabled=feature_state.enabled,
        value=value,
        identity_id=feature_state.identity_id,
        identity_identifier=getattr(feature_state.identity, "identifier", None),
        feature_segment=feature_state.feature_segment,
        multivariate_feature_state_values=mv_values,
    )


def _get_previous_multivariate_values(
    feature_state: FeatureState,
) -> list[MultivariateFeatureStateValue]:
    """Get previous multivariate values from history."""
    mv_values: list[MultivariateFeatureStateValue] = []
    for mv in MultivariateFeatureStateValue.objects.filter(
        feature_state_id=feature_state.id
    ):
        history = mv.history.first()
        if history and history.prev_record:
            mv_values.append(history.prev_record.instance)
        else:
            # No previous record, use current value
            mv_values.append(mv)
    return mv_values


@register_task_handler()
def delete_feature(feature_id: int) -> None:
    Feature.objects.get(pk=feature_id).delete()

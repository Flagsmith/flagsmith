from environments.models import Webhook
from features.models import FeatureState
from integrations.github.tasks import call_github_app_webhook_for_feature_state
from webhooks.constants import WEBHOOK_DATETIME_FORMAT
from webhooks.webhooks import (
    WebhookEventType,
    call_environment_webhooks,
    call_organisation_webhooks,
)

from .models import HistoricalFeatureState


def trigger_feature_state_change_webhooks(
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
        str(history_instance.history_user)
        if history_instance and history_instance.history_user
        else ""
    )

    new_state = (
        None
        if event_type == WebhookEventType.FLAG_DELETED
        else _get_feature_state_webhook_data(instance)
    )
    data = {"new_state": new_state, "changed_by": changed_by, "timestamp": timestamp}
    previous_state = _get_previous_state(history_instance, event_type)
    print(
        "DEBUG: trigger_feature_state_change_webhooks:",
        history_instance.environment.api_key,
    )

    if previous_state:
        data.update(previous_state=previous_state)

    call_environment_webhooks.delay(
        args=(instance.environment.id, data, event_type.value)
    )

    call_organisation_webhooks.delay(
        args=(
            instance.environment.project.organisation.id,
            data,
            event_type.value,
        )
    )

    if hasattr(instance.environment.project.organisation, "github_config"):
        github_configuration = instance.environment.project.organisation.github_config

        feature_data = {
            "id": history_instance.feature.id,
            "name": history_instance.feature.name,
            "feature_states": [],
        }
        feature_data["installation_id"] = github_configuration.installation_id
        feature_data["organisation_id"] = github_configuration.organisation.id

        feature_state = {
            "environment_name": new_state["environment"]["name"],
            "feature_value": new_state["enabled"],
        }

        if instance.feature_state_value.string_value is not None:
            feature_state["string_value"] = instance.feature_state_value.string_value
        if instance.feature_state_value.boolean_value is not None:
            feature_state["boolean_value"] = instance.feature_state_value.boolean_value
        if instance.feature_state_value.integer_value is not None:
            feature_state["integer_value"] = instance.feature_state_value.integer_value
        if (
            hasattr(feature_state, "feature_segment")
            and instance.feature_segment is not None
        ):
            feature_state["segment_name"] = instance.feature_segment.segment.name

        feature_data["feature_states"].append(feature_state)

        call_github_app_webhook_for_feature_state.delay(
            args=(
                feature_data,
                event_type.value,
            ),
        )
    else:
        print(
            "No GitHub integration exists for organisation %d. Not calling webhooks.",
            instance.environment.project.organisation.id,
        )
        return


def _get_previous_state(
    history_instance: HistoricalFeatureState, event_type: WebhookEventType
) -> dict:
    if event_type == WebhookEventType.FLAG_DELETED:
        return _get_feature_state_webhook_data(history_instance.instance)
    if history_instance and history_instance.prev_record:
        return _get_feature_state_webhook_data(
            history_instance.prev_record.instance, previous=True
        )
    return None


def _get_feature_state_webhook_data(feature_state, previous=False):
    # TODO: fix circular imports and use serializers instead.
    feature_state_value = (
        feature_state.get_feature_state_value()
        if not previous
        else feature_state.previous_feature_state_value
    )

    return Webhook.generate_webhook_feature_state_data(
        feature_state.feature,
        environment=feature_state.environment,
        enabled=feature_state.enabled,
        value=feature_state_value,
        identity_id=feature_state.identity_id,
        identity_identifier=getattr(feature_state.identity, "identifier", None),
        feature_segment=feature_state.feature_segment,
    )

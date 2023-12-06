from datetime import timedelta
from threading import Thread

from django.utils import timezone

from environments.models import Webhook
from features.models import Feature, FeatureState
from projects.models import Project
from projects.tags.models import Tag
from task_processor.decorators import register_recurring_task
from webhooks.constants import WEBHOOK_DATETIME_FORMAT
from webhooks.webhooks import (
    WebhookEventType,
    call_environment_webhooks,
    call_organisation_webhooks,
)

from .constants import STALE_FLAGS_TAG_LABEL
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
    if previous_state:
        data.update(previous_state=previous_state)
    Thread(
        target=call_environment_webhooks,
        args=(instance.environment, data, event_type),
    ).start()

    Thread(
        target=call_organisation_webhooks,
        args=(
            instance.environment.project.organisation,
            data,
            event_type,
        ),
    ).start()


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


@register_recurring_task(run_every=timedelta(hours=3))
def tag_stale_flags():
    feature_tag_relationships = []

    for project in Project.objects.filter(environments__use_v2_feature_versioning=True):
        # TODO: can we centralise this query to get stale flags (FeatureManager?)
        stale_flags = project.features.exclude(tags__is_permanent=True).filter(
            feature_states__environment_feature_version__created_at__lt=timezone.now()
            - timedelta(days=project.stale_flags_limit_days)
        )

        # TODO: should we delegate each project to a separate regular task?
        if stale_flags.exists():
            stale_flags_tag, _ = Tag.objects.get_or_create(
                label=STALE_FLAGS_TAG_LABEL, project=project, is_system_tag=True
            )
            feature_tag_relationships.extend(
                Feature.tags.through(feature=feature, tag=stale_flags_tag)
                for feature in stale_flags.exclude(tags=stale_flags_tag)
            )

    Feature.tags.through.objects.bulk_create(feature_tag_relationships)

from django.dispatch import receiver
from simple_history.signals import post_create_historical_record

from webhooks.webhooks import call_environment_webhooks, WebhookEventType, call_organisation_webhooks
from .models import HistoricalFeatureState
from .serializers import (
    FeatureStateSerializerFullWithIdentity,
)


@receiver(post_create_historical_record, sender=HistoricalFeatureState)
def trigger_webhook_for_feature_state_change(
        sender, instance, history_instance, **kwargs
):
    # If the instance is null, return
    if instance is None:
        return

    # Not entirely sure why this is necessary but we seem to be getting ~3 signals being triggered when updating a
    # flag, this filters 2 of them out. Need to rewrite this whole function.
    if not kwargs.get('history_user'):
        return

    # If there is no environment on this instance
    if not hasattr(instance, "environment"):
        return

    changing_user = kwargs.get("history_user")
    if changing_user:
        changed_by = changing_user.first_name + " " + changing_user.last_name
    else:
        changed_by = ""

    data = {
        "new_state": FeatureStateSerializerFullWithIdentity(instance=instance).data,
        "changed_by": changed_by,
        "timestamp": kwargs.get("history_date"),
    }

    if history_instance.prev_record:
        data["previous_state"] = FeatureStateSerializerFullWithIdentity(
            instance=history_instance.prev_record.instance
        ).data

    call_environment_webhooks(instance.environment, data, WebhookEventType.FLAG_UPDATED)
    call_organisation_webhooks(instance.environment.project.organisation, data, WebhookEventType.FLAG_UPDATED)

from django.dispatch import receiver
from simple_history.signals import post_create_historical_record

from .models import HistoricalFeatureState
from .serializers import FeatureStateSerializerFull
from webhooks.webhooks import call_webhook


@receiver(post_create_historical_record, sender=HistoricalFeatureState)
def trigger_webhook_for_feature_state_change(sender, instance, history_instance, **kwargs):
    env = instance.environment

    if not env.webhooks_enabled:
        return

    changing_user = kwargs.get("history_user")
    if changing_user:
        changed_by = changing_user.first_name + " " + changing_user.last_name
    else:
        changed_by = ""

    data = {
        "event_type": "FLAG_UPDATED",
        "data": {
            "new_state": FeatureStateSerializerFull(instance=instance).data,
            "changed_by": changed_by,
            "timestamp": kwargs.get("history_date")
        }
    }

    call_webhook(env, data)

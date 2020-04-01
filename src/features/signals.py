import logging

from django.dispatch import receiver
from simple_history.signals import post_create_historical_record

from environments.models import Environment, Identity
from webhooks.webhooks import call_environment_webhooks, WebhookEventType, call_organisation_webhooks
from .models import HistoricalFeatureState
from .serializers import (
    FeatureStateSerializerFullWithIdentity,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@receiver(post_create_historical_record, sender=HistoricalFeatureState)
def trigger_webhook_for_feature_state_change(
        sender, instance, history_instance, **kwargs
):
    try:
        # If the instance is null, return
        if instance is None:
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

    except Environment.DoesNotExist:
        logger.error("Got an Environment.DoesNotExist error calling the webhook for instance id %d." % instance.id)

    except Identity.DoesNotExist:
        logger.error("Got an Identity.DoesNotExist error calling the webhook for instance id %d." % instance.id)

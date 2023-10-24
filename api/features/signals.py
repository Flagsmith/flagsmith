import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

# noinspection PyUnresolvedReferences
from .models import FeatureState
from .tasks import trigger_feature_state_change_webhooks

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FeatureState)
def trigger_feature_state_change_webhooks_signal(instance, **kwargs):
    if instance.environment_feature_version_id:
        return
    trigger_feature_state_change_webhooks(instance)

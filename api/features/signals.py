import logging

from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

# noinspection PyUnresolvedReferences
from .models import FeatureState
from .tasks import trigger_feature_state_change_webhooks

logger = logging.getLogger(__name__)

feature_state_change_went_live = Signal()


@receiver(post_save, sender=FeatureState)
def trigger_feature_state_change_webhooks_signal(instance, **kwargs):  # type: ignore[no-untyped-def]
    if instance.environment_feature_version_id or instance.deleted_at:
        return
    trigger_feature_state_change_webhooks(instance)

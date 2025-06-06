from django.db.models.signals import post_save
from django.dispatch import receiver

from features.models import FeatureState

from .tasks import send_sentry_change_tracking_webhook_update


@receiver(post_save, sender=FeatureState)
def trigger_feature_state_change_sentry_change_tracking(instance, **kwargs):  # type: ignore[no-untyped-def]
    send_sentry_change_tracking_webhook_update.delay(args=(instance.pk,))

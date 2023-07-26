import copy
import hashlib
import time
import uuid

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from features.models import FeatureState
from features.versioning.models import EnvironmentFeatureVersion


@receiver(post_save, sender=EnvironmentFeatureVersion)
def add_existing_feature_states(instance, created, **kwargs):
    if not created:
        return

    previous_environment_feature_version = instance.get_previous_version()
    if not previous_environment_feature_version:
        return

    feature_states = []
    for feature_state in previous_environment_feature_version.feature_states.all():
        new_feature_state = copy.deepcopy(feature_state)
        new_feature_state.id = None
        new_feature_state.environment_feature_version = instance
        new_feature_state.uuid = uuid.uuid4()
        feature_states.append(new_feature_state)

    FeatureState.objects.bulk_create(feature_states)


@receiver(pre_save, sender=EnvironmentFeatureVersion)
def generate_sha(instance, **kwargs):
    if not instance.sha:
        instance.sha = hashlib.sha256(
            f"{instance.environment.id}{instance.feature.id}{time.time()}".encode(
                "utf-8"
            )
        ).hexdigest()


@receiver(pre_save, sender=EnvironmentFeatureVersion)
def update_live_from(instance, **kwargs):
    if instance.published and not instance.live_from:
        instance.live_from = timezone.now()

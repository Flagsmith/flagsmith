from django.db.models.signals import post_init, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from environments.tasks import rebuild_environment_document
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.signals import environment_feature_version_published
from features.versioning.tasks import (
    create_environment_feature_version_published_audit_log_task,
    trigger_update_version_webhooks,
)


@receiver(post_save, sender=EnvironmentFeatureVersion)
def add_existing_feature_states(  # type: ignore[no-untyped-def]
    instance: EnvironmentFeatureVersion, created: bool, **kwargs
):
    if not created:
        return

    previous_environment_feature_version = instance.get_previous_version()
    if not previous_environment_feature_version:
        return

    for feature_state in previous_environment_feature_version.feature_states.all():
        feature_state.clone(
            env=instance.environment, environment_feature_version=instance
        )


@receiver(pre_save, sender=EnvironmentFeatureVersion)
def update_live_from(instance: EnvironmentFeatureVersion, **kwargs):  # type: ignore[no-untyped-def]
    if instance.published and not instance.live_from:
        instance.live_from = timezone.now()


@receiver(post_init, sender=EnvironmentFeatureVersion)
def cache_fields(instance: EnvironmentFeatureVersion, **kwargs):  # type: ignore[no-untyped-def]
    instance._init_fields = {"published": instance.published}


@receiver(environment_feature_version_published, sender=EnvironmentFeatureVersion)
def update_environment_document(instance: EnvironmentFeatureVersion, **kwargs):  # type: ignore[no-untyped-def]
    rebuild_environment_document.delay(
        kwargs={"environment_id": instance.environment_id},
        delay_until=instance.live_from,
    )


@receiver(environment_feature_version_published, sender=EnvironmentFeatureVersion)
def trigger_webhooks(instance: EnvironmentFeatureVersion, **kwargs) -> None:  # type: ignore[no-untyped-def]
    trigger_update_version_webhooks.delay(
        kwargs={"environment_feature_version_uuid": str(instance.uuid)},
        delay_until=instance.live_from,
    )


@receiver(environment_feature_version_published, sender=EnvironmentFeatureVersion)
def create_environment_feature_version_published_audit_log(  # type: ignore[no-untyped-def]
    instance: EnvironmentFeatureVersion, **kwargs
) -> None:
    create_environment_feature_version_published_audit_log_task.delay(
        kwargs={"environment_feature_version_uuid": str(instance.uuid)}
    )

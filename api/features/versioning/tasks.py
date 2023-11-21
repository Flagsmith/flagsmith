import logging
import typing

from django.utils import timezone

from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.schemas import (
    EnvironmentFeatureVersionWebhookDataSerializer,
)
from features.versioning.versioning_service import (
    get_environment_flags_queryset,
)
from task_processor.decorators import register_task_handler
from webhooks.webhooks import WebhookEventType, call_environment_webhooks

if typing.TYPE_CHECKING:
    from environments.models import Environment


logger = logging.getLogger(__name__)
environment_feature_version_webhook_schema = (
    EnvironmentFeatureVersionWebhookDataSerializer()
)


@register_task_handler()
def enable_v2_versioning(environment_id: int):
    from environments.models import Environment

    environment = Environment.objects.get(id=environment_id)

    _create_initial_feature_versions(environment)

    environment.use_v2_feature_versioning = True
    environment.save()


def _create_initial_feature_versions(environment: "Environment"):
    from features.models import Feature

    now = timezone.now()

    for feature in Feature.objects.filter(project=environment.project_id):
        ef_version = EnvironmentFeatureVersion.objects.create(
            feature=feature,
            environment=environment,
            published_at=now,
            live_from=now,
        )
        get_environment_flags_queryset(environment=environment).filter(
            identity__isnull=True, feature=feature
        ).update(environment_feature_version=ef_version)


@register_task_handler()
def trigger_update_version_webhooks(environment_feature_version_uuid: str) -> None:
    environment_feature_version = EnvironmentFeatureVersion.objects.get(
        uuid=environment_feature_version_uuid
    )
    if not environment_feature_version.is_live:
        logger.exception("Feature version has not been published.")
        return

    data = environment_feature_version_webhook_schema.dump(environment_feature_version)
    call_environment_webhooks(
        environment=environment_feature_version.environment,
        data=data,
        event_type=WebhookEventType.NEW_VERSION_PUBLISHED,
    )

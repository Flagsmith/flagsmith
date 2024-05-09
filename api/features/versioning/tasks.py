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
def enable_v2_versioning(environment_id: int) -> None:
    from environments.models import Environment

    environment = Environment.objects.get(id=environment_id)

    _create_initial_feature_versions(environment)

    environment.use_v2_feature_versioning = True
    environment.save()


@register_task_handler()
def disable_v2_versioning(environment_id: int) -> None:
    from environments.models import Environment
    from features.models import FeatureSegment, FeatureState
    from features.versioning.models import EnvironmentFeatureVersion

    environment = Environment.objects.get(id=environment_id)

    latest_feature_states = get_environment_flags_queryset(environment)

    # delete any feature states associated with older versions
    FeatureState.objects.filter(identity_id__isnull=True).exclude(
        id__in=[fs.id for fs in latest_feature_states]
    ).delete()

    # update the latest feature states (and respective feature segments) to be the
    # latest version according to the old versioning system
    latest_feature_states.update(
        version=1, live_from=timezone.now(), environment_feature_version=None
    )
    FeatureSegment.objects.filter(environment=environment).update(
        environment_feature_version=None
    )

    EnvironmentFeatureVersion.objects.filter(environment=environment).delete()

    environment.use_v2_feature_versioning = False
    environment.save()


def _create_initial_feature_versions(environment: "Environment"):
    from features.models import Feature, FeatureSegment

    now = timezone.now()

    for feature in Feature.objects.filter(project=environment.project_id):
        ef_version = EnvironmentFeatureVersion.objects.create(
            feature=feature,
            environment=environment,
            published_at=now,
            live_from=now,
        )

        latest_feature_states = get_environment_flags_queryset(
            environment=environment
        ).filter(identity__isnull=True, feature=feature)
        related_feature_segments = FeatureSegment.objects.filter(
            feature_states__in=latest_feature_states
        )

        latest_feature_states.update(environment_feature_version=ef_version)
        related_feature_segments.update(environment_feature_version=ef_version)


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

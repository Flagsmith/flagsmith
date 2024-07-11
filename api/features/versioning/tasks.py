import json
import logging
import typing

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from audit.constants import ENVIRONMENT_FEATURE_VERSION_PUBLISHED_MESSAGE
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from features.models import FeatureState
from features.versioning.models import (
    EnvironmentFeatureVersion,
    VersionChangeSet,
)
from features.versioning.schemas import (
    EnvironmentFeatureVersionWebhookDataSerializer,
)
from features.versioning.versioning_service import (
    get_environment_flags_queryset,
)
from task_processor.decorators import register_task_handler
from users.models import FFAdminUser
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
    latest_feature_state_ids = [fs.id for fs in latest_feature_states]

    # delete any feature states and feature segments associated with older versions
    FeatureState.objects.filter(
        identity_id__isnull=True, environment=environment
    ).exclude(id__in=latest_feature_state_ids).delete()
    FeatureSegment.objects.filter(environment=environment).exclude(
        feature_states__id__in=latest_feature_state_ids
    ).delete()

    # update the latest feature states (and respective feature segments) to be the
    # latest version according to the old versioning system
    latest_feature_states.update(
        version=1, live_from=timezone.now(), environment_feature_version=None
    )
    FeatureSegment.objects.filter(
        environment=environment, feature_states__id__in=latest_feature_state_ids
    ).update(environment_feature_version=None)

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
            environment=environment, feature_name=feature.name
        ).filter(identity__isnull=True)
        related_feature_segments = FeatureSegment.objects.filter(
            feature_states__in=latest_feature_states
        )

        latest_feature_states.update(environment_feature_version=ef_version)
        related_feature_segments.update(environment_feature_version=ef_version)

        scheduled_feature_states = FeatureState.objects.filter(
            live_from__gt=now,
            change_request__isnull=False,
            change_request__committed_at__isnull=False,
            change_request__deleted_at__isnull=True,
        ).select_related("change_request")
        for feature_state in scheduled_feature_states:
            ef_version = EnvironmentFeatureVersion.objects.create(
                feature=feature,
                environment=environment,
                published_at=feature_state.change_request.committed_at,
                live_from=feature_state.live_from,
                change_request=feature_state.change_request,
            )
            feature_state.environment_feature_version = ef_version
            feature_state.change_request = None

        FeatureState.objects.bulk_update(
            scheduled_feature_states,
            fields=["environment_feature_version", "change_request"],
        )


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
        environment_id=environment_feature_version.environment_id,
        data=data,
        event_type=WebhookEventType.NEW_VERSION_PUBLISHED.value,
    )


@register_task_handler()
def create_environment_feature_version_published_audit_log_task(
    environment_feature_version_uuid: str,
) -> None:
    environment_feature_version = EnvironmentFeatureVersion.objects.select_related(
        "environment", "feature"
    ).get(uuid=environment_feature_version_uuid)

    AuditLog.objects.create(
        environment=environment_feature_version.environment,
        related_object_type=RelatedObjectType.EF_VERSION.name,
        related_object_uuid=environment_feature_version.uuid,
        log=ENVIRONMENT_FEATURE_VERSION_PUBLISHED_MESSAGE
        % environment_feature_version.feature.name,
        author_id=environment_feature_version.published_by_id,
        master_api_key_id=environment_feature_version.published_by_api_key_id,
    )


@register_task_handler()
def publish_version_change_set(
    version_change_set_id: int, user_id: int, is_scheduled: bool = False
) -> None:
    version_change_set = VersionChangeSet.objects.select_related(
        "change_request", "change_request__user"
    ).get(id=version_change_set_id)
    user = FFAdminUser.objects.get(id=user_id)

    if is_scheduled and version_change_set.get_conflicts():
        _send_failed_due_to_conflict_alert_to_change_request_author(version_change_set)
        return

    # TODO:
    #  - using the serializer here is kinda hacky, is there another abstraction layer we can add
    #  (and reuse in the serializer as well perhaps?)

    from features.versioning.serializers import (
        EnvironmentFeatureVersionCreateSerializer,
    )

    serializer = EnvironmentFeatureVersionCreateSerializer(
        data={
            "feature_states_to_create": (
                json.loads(version_change_set.feature_states_to_create)
                if version_change_set.feature_states_to_create
                else []
            ),
            "feature_states_to_update": (
                json.loads(version_change_set.feature_states_to_update)
                if version_change_set.feature_states_to_update
                else []
            ),
            "segment_ids_to_delete_overrides": (
                json.loads(version_change_set.segment_ids_to_delete_overrides)
                if version_change_set.segment_ids_to_delete_overrides
                else []
            ),
        }
    )
    serializer.is_valid(raise_exception=True)
    version: EnvironmentFeatureVersion = serializer.save(
        feature=version_change_set.feature,
        environment=version_change_set.environment,
        created_by=user,
    )
    version.publish(
        published_by=user, live_from=version_change_set.live_from or timezone.now()
    )

    version_change_set.published_at = version_change_set.live_from = timezone.now()
    version_change_set.published_by = user
    version_change_set.save()


def _send_failed_due_to_conflict_alert_to_change_request_author(
    version_change_set: VersionChangeSet,
) -> None:
    context = {
        "change_request": version_change_set.change_request,
        "user": version_change_set.change_request.user,
        "feature": version_change_set.feature,
    }
    send_mail(
        subject=version_change_set.change_request.email_subject,
        message=render_to_string(
            "versioning/scheduled_change_failed_conflict_email.txt", context
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[version_change_set.change_request.user.email],
    )

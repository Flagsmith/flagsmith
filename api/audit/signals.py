import logging
from typing import TYPE_CHECKING, Any, Callable, Literal, Protocol, Type

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.serializers import AuditLogListSerializer
from audit.services import get_audited_instance_from_audit_log_record
from features.models import FeatureState, FeatureStateValue
from features.multivariate.models import MultivariateFeatureStateValue
from features.signals import feature_state_change_went_live
from integrations.common.models import IntegrationsModel
from integrations.datadog.datadog import DataDogWrapper
from integrations.dynatrace.dynatrace import DynatraceWrapper
from integrations.grafana.grafana import GrafanaWrapper
from integrations.new_relic.new_relic import NewRelicWrapper
from integrations.sentry.change_tracking import SentryChangeTracking
from integrations.sentry.models import SentryChangeTrackingConfiguration
from integrations.slack.slack import SlackWrapper
from organisations.models import OrganisationWebhook
from webhooks.tasks import call_organisation_webhooks
from webhooks.webhooks import WebhookEventType

if TYPE_CHECKING:
    from integrations.datadog.models import DataDogConfiguration


logger = logging.getLogger(__name__)


AuditLogIntegrationAttrName = Literal[
    "data_dog_config",
    "dynatrace_config",
    "grafana_config",
    "new_relic_config",
    "slack_config",
]


class _AuditLogSignalHandler(Protocol):
    def __call__(
        self,
        sender: Type[AuditLog],
        instance: AuditLog,
        **kwargs: Any,
    ) -> None: ...


_DecoratedSignal = Callable[[_AuditLogSignalHandler], _AuditLogSignalHandler]


def _get_integration_config(
    instance: AuditLog,
    integration_name: AuditLogIntegrationAttrName,
) -> IntegrationsModel | None:
    for relation_name in ("project", "environment", "organisation"):
        if hasattr(
            related_object := getattr(instance, relation_name),
            integration_name,
        ):
            integration_config: IntegrationsModel = getattr(
                related_object,
                integration_name,
            )
            if not integration_config.deleted:
                return integration_config
    return None


@receiver(post_save, sender=AuditLog)
def call_webhooks(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    if settings.DISABLE_WEBHOOKS:
        return

    if not (instance.project_id or instance.environment_id):
        logger.warning("Audit log without project or environment. Not sending webhook.")
        return

    organisation_id = (
        instance.project.organisation_id
        if instance.project
        else instance.environment.project.organisation_id
    )

    if OrganisationWebhook.objects.filter(
        organisation_id=organisation_id, enabled=True
    ).exists():
        data = AuditLogListSerializer(instance=instance).data
        call_organisation_webhooks.delay(
            args=(organisation_id, data, WebhookEventType.AUDIT_LOG_CREATED.value)
        )


def track_only(types: list[RelatedObjectType]) -> _DecoratedSignal:
    """
    Restrict an AuditLog signal to a certain list of RelatedObjectType
    """

    def decorator(signal_function: _AuditLogSignalHandler) -> _AuditLogSignalHandler:
        def signal_wrapper(
            sender: Type[AuditLog],
            instance: AuditLog,
            **kwargs: Any,
        ) -> None:
            type_names = (t.name for t in types)
            if instance.related_object_type not in type_names:
                return None
            return signal_function(sender, instance, **kwargs)

        return signal_wrapper

    return decorator


def track_only_feature_related_events(signal_function):  # type: ignore[no-untyped-def]
    allowed_types = [
        RelatedObjectType.FEATURE,
        RelatedObjectType.FEATURE_STATE,
        RelatedObjectType.SEGMENT,
        RelatedObjectType.EF_VERSION,
    ]
    return track_only(allowed_types)(signal_function)


def _track_event_async(instance, integration_client):  # type: ignore[no-untyped-def]
    if event_data := integration_client.generate_event_data(audit_log_record=instance):
        integration_client.track_event_async(event=event_data)
        return


@receiver(post_save, sender=AuditLog)
@track_only_feature_related_events
def send_audit_log_event_to_datadog(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    data_dog_config: "DataDogConfiguration | None" = _get_integration_config(
        instance, "data_dog_config"
    )

    if not data_dog_config:
        return

    data_dog = DataDogWrapper(
        base_url=data_dog_config.base_url,  # type: ignore[arg-type]
        api_key=data_dog_config.api_key,
        use_custom_source=data_dog_config.use_custom_source,
    )
    _track_event_async(instance, data_dog)  # type: ignore[no-untyped-call]


@receiver(post_save, sender=AuditLog)
@track_only_feature_related_events
def send_audit_log_event_to_new_relic(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    new_relic_config = _get_integration_config(instance, "new_relic_config")
    if not new_relic_config:
        return

    new_relic = NewRelicWrapper(
        base_url=new_relic_config.base_url,  # type: ignore[arg-type]
        api_key=new_relic_config.api_key,
        app_id=new_relic_config.app_id,
    )
    _track_event_async(instance, new_relic)  # type: ignore[no-untyped-call]


@receiver(post_save, sender=AuditLog)
@track_only_feature_related_events
def send_audit_log_event_to_dynatrace(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    dynatrace_config = _get_integration_config(instance, "dynatrace_config")
    if not dynatrace_config:
        return

    dynatrace = DynatraceWrapper(
        base_url=dynatrace_config.base_url,  # type: ignore[arg-type]
        api_key=dynatrace_config.api_key,
        entity_selector=dynatrace_config.entity_selector,
    )
    _track_event_async(instance, dynatrace)  # type: ignore[no-untyped-call]


@receiver(post_save, sender=AuditLog)
@track_only_feature_related_events
def send_audit_log_event_to_grafana(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    grafana_config = _get_integration_config(instance, "grafana_config")
    if not grafana_config:
        return

    grafana = GrafanaWrapper(
        base_url=grafana_config.base_url,  # type: ignore[arg-type]
        api_key=grafana_config.api_key,
    )
    _track_event_async(instance, grafana)  # type: ignore[no-untyped-call]


@receiver(post_save, sender=AuditLog)
@track_only_feature_related_events
def send_audit_log_event_to_slack(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    slack_project_config = _get_integration_config(instance, "slack_config")
    if not slack_project_config:
        return
    env_config = slack_project_config.env_config.filter(
        environment=instance.environment, enabled=True
    ).first()
    if not env_config:
        return
    slack = SlackWrapper(
        api_token=slack_project_config.api_token, channel_id=env_config.channel_id
    )
    _track_event_async(instance, slack)  # type: ignore[no-untyped-call]


@receiver(post_save, sender=AuditLog)
@track_only([RelatedObjectType.FEATURE_STATE])
def send_feature_flag_went_live_signal(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    audited_instance = get_audited_instance_from_audit_log_record(instance)

    # Handle FeatureState, FeatureStateValue, and MultivariateFeatureStateValue audit logs
    # All these types have related_object_type=FEATURE_STATE
    if isinstance(audited_instance, (FeatureStateValue, MultivariateFeatureStateValue)):
        feature_state = audited_instance.feature_state
    elif isinstance(audited_instance, FeatureState):
        feature_state = audited_instance
    else:
        return

    if feature_state.is_scheduled:
        return  # This is handled by audit.tasks.create_feature_state_went_live_audit_log

    feature_state_change_went_live.send(feature_state, audit_log=instance)


@receiver(feature_state_change_went_live)
def send_audit_log_event_to_sentry(
    sender: FeatureState, audit_log: AuditLog, **kwargs: Any
) -> None:
    try:
        sentry_configuration = SentryChangeTrackingConfiguration.objects.get(
            environment=audit_log.environment,
            deleted_at__isnull=True,
        )
    except SentryChangeTrackingConfiguration.DoesNotExist:
        return

    sentry_change_tracking = SentryChangeTracking(
        webhook_url=sentry_configuration.webhook_url,
        secret=sentry_configuration.secret,
    )

    _track_event_async(audit_log, sentry_change_tracking)  # type: ignore[no-untyped-call]


@receiver(post_save, sender=AuditLog)
@track_only([RelatedObjectType.EF_VERSION])
def send_efv_audit_log_event_to_sentry(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    """
    Sentry's flag-log API needs per-FS payloads. v2 EFV publish emits a single
    EF_VERSION-typed audit row representing N feature state changes, so expand
    it into per-FS Sentry entries and send them as a single batched payload.
    """
    from features.versioning.models import EnvironmentFeatureVersion
    from features.versioning.versioning_service import (
        get_updated_feature_states_for_version,
    )

    try:
        sentry_configuration = SentryChangeTrackingConfiguration.objects.get(
            environment=instance.environment,
            deleted_at__isnull=True,
        )
    except SentryChangeTrackingConfiguration.DoesNotExist:
        return

    if not instance.related_object_uuid:
        return

    try:
        efv = EnvironmentFeatureVersion.objects.select_related("feature").get(
            uuid=instance.related_object_uuid,
        )
    except EnvironmentFeatureVersion.DoesNotExist:
        return

    changed_feature_states = get_updated_feature_states_for_version(efv)
    if not changed_feature_states:
        return

    previous_version = efv.get_previous_version()
    previous_fs_keys: set[tuple[int | None, int | None]] = set()
    if previous_version:
        previous_fs_keys = {
            (
                fs.identity_id,
                fs.feature_segment.segment_id if fs.feature_segment else None,
            )
            for fs in previous_version.feature_states.all()
        }

    timestamp = (efv.live_from or efv.published_at or instance.created_date)
    author_email = getattr(instance.author, "email", "app@flagsmith.com")

    events: list[dict[str, Any]] = []
    for fs in changed_feature_states:
        key = (
            fs.identity_id,
            fs.feature_segment.segment_id if fs.feature_segment else None,
        )
        action = "updated" if key in previous_fs_keys else "created"
        events.append(
            {
                "action": action,
                "flag": efv.feature.name,
                "created_at": timestamp.isoformat(timespec="seconds"),
                "created_by": {
                    "id": author_email,
                    "type": "email",
                },
                "change_id": str(fs.pk),
            }
        )

    sentry_change_tracking = SentryChangeTracking(
        webhook_url=sentry_configuration.webhook_url,
        secret=sentry_configuration.secret,
    )
    sentry_change_tracking.track_events_async(events)


@receiver(post_save, sender=FeatureState)
def send_v2_initial_feature_state_event_to_sentry(  # type: ignore[no-untyped-def]
    sender,
    instance: FeatureState,
    created: bool,
    **kwargs: Any,
) -> None:
    """
    v2 envs suppress FS-typed audit rows for auto-created initial FeatureStates,
    and `create_initial_version` doesn't fire `environment_feature_version_published`,
    so Sentry has no audit row to latch onto for flag-create in v2 envs.
    Listen directly to FS post_save for v2 env-default FSes that belong to an
    initial (no-previous-version) EFV and emit a Sentry "created" event with the
    FS pk as change_id. The author is recovered from the FEATURE audit row
    written moments earlier in the same flow.
    """
    if not created:
        return
    if instance.environment_feature_version_id is None:
        return
    if instance.feature_segment_id or instance.identity_id:
        return

    efv = instance.environment_feature_version
    if efv is None or efv.get_previous_version() is not None:
        return

    try:
        sentry_configuration = SentryChangeTrackingConfiguration.objects.get(
            environment=instance.environment,
            deleted_at__isnull=True,
        )
    except SentryChangeTrackingConfiguration.DoesNotExist:
        return

    feature_audit_log = (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FEATURE.name,
            related_object_id=instance.feature_id,
        )
        .order_by("-id")
        .first()
    )
    author_email = (
        feature_audit_log.author.email
        if feature_audit_log and feature_audit_log.author
        else "app@flagsmith.com"
    )

    timestamp = (
        max(instance.live_from, instance.updated_at)
        if instance.live_from
        else instance.updated_at
    )

    events = [
        {
            "action": "created",
            "flag": instance.feature.name,
            "created_at": timestamp.isoformat(timespec="seconds"),
            "created_by": {
                "id": author_email,
                "type": "email",
            },
            "change_id": str(instance.pk),
        }
    ]

    sentry_change_tracking = SentryChangeTracking(
        webhook_url=sentry_configuration.webhook_url,
        secret=sentry_configuration.secret,
    )
    sentry_change_tracking.track_events_async(events)


@receiver(feature_state_change_went_live)
def trigger_feature_state_change_webhooks(
    sender: FeatureState,
    **kwargs: Any,
) -> None:
    """
    Trigger FLAG_UPDATED webhooks when a feature state change goes live.

    Triggered from AuditLog post_save. Fetches a fresh feature state from the
    database to ensure we get the latest data (including FeatureStateValue),
    since drf-writable-nested saves the parent before nested objects.
    """
    from features import tasks

    # Fetch fresh data from the database to ensure we have the latest state
    # This is necessary because:
    # 1. drf-writable-nested saves FeatureState before FeatureStateValue
    # 2. The history record's instance may have stale cached values
    try:
        fresh_feature_state = FeatureState.objects.get(id=sender.id)
    except FeatureState.DoesNotExist:
        # Skip deleted feature states - handled in views
        return

    # Skip versioned environments - handled by trigger_update_version_webhooks
    if fresh_feature_state.environment_feature_version_id:
        return

    tasks.trigger_feature_state_change_webhooks(fresh_feature_state)

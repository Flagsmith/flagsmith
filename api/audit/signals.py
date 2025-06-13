import logging
from typing import Any, Callable, Literal, Protocol, Type

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.serializers import AuditLogListSerializer
from audit.services import get_audited_instance_from_audit_log_record
from features.models import FeatureState
from features.signals import feature_state_change_went_live
from integrations.common.exceptions import InvalidIntegrationParameters
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
    try:
        event_data = integration_client.generate_event_data(audit_log_record=instance)
    except InvalidIntegrationParameters as error:  # pragma: no cover
        logger.error("Cannot prepare integration: %s", repr(error))
        return

    integration_client.track_event_async(event=event_data)


@receiver(post_save, sender=AuditLog)
@track_only_feature_related_events
def send_audit_log_event_to_datadog(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
    data_dog_config = _get_integration_config(instance, "data_dog_config")

    if not data_dog_config:
        return

    data_dog = DataDogWrapper(
        base_url=data_dog_config.base_url,  # type: ignore[arg-type]
        api_key=data_dog_config.api_key,
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
    feature_state = get_audited_instance_from_audit_log_record(instance)
    if not (feature_state and isinstance(feature_state, FeatureState)):
        return

    if feature_state.is_scheduled:
        return  # This is handled by audit.tasks.create_feature_state_went_live_audit_log

    feature_state_change_went_live.send(instance)


@receiver(feature_state_change_went_live)
def send_audit_log_event_to_sentry(sender: AuditLog, **kwargs: Any) -> None:
    try:
        sentry_configuration = SentryChangeTrackingConfiguration.objects.get(
            environment=sender.environment,
            deleted_at__isnull=True,
        )
    except SentryChangeTrackingConfiguration.DoesNotExist:
        return

    sentry_change_tracking = SentryChangeTracking(
        webhook_url=sentry_configuration.webhook_url,
        secret=sentry_configuration.secret,
    )

    _track_event_async(sender, sentry_change_tracking)  # type: ignore[no-untyped-call]

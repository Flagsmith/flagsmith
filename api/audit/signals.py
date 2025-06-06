import logging
import typing

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from audit.models import AuditLog, RelatedObjectType  # type: ignore[attr-defined]
from audit.serializers import AuditLogListSerializer
from integrations.common.models import IntegrationsModel
from integrations.datadog.datadog import DataDogWrapper
from integrations.dynatrace.dynatrace import DynatraceWrapper
from integrations.grafana.grafana import GrafanaWrapper
from integrations.new_relic.new_relic import NewRelicWrapper
from integrations.slack.slack import SlackWrapper
from organisations.models import OrganisationWebhook
from webhooks.tasks import call_organisation_webhooks
from webhooks.webhooks import WebhookEventType

logger = logging.getLogger(__name__)


AuditLogIntegrationAttrName = typing.Literal[
    "data_dog_config",
    "dynatrace_config",
    "grafana_config",
    "new_relic_config",
    "slack_config",
]


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


def track_only_feature_related_events(signal_function):  # type: ignore[no-untyped-def]
    def signal_wrapper(sender, instance, **kwargs):  # type: ignore[no-untyped-def]
        # Only handle Feature related changes
        if instance.related_object_type not in [
            RelatedObjectType.FEATURE.name,
            RelatedObjectType.FEATURE_STATE.name,
            RelatedObjectType.SEGMENT.name,
            RelatedObjectType.EF_VERSION.name,
        ]:
            return None
        return signal_function(sender, instance, **kwargs)

    return signal_wrapper


def _track_event_async(instance, integration_client):  # type: ignore[no-untyped-def]
    event_data = integration_client.generate_event_data(audit_log_record=instance)

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

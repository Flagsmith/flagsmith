import logging

import boto3
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from flag_engine.environments.builders import build_environment_dict

from audit.models import AuditLog, RelatedObjectType
from audit.serializers import AuditLogSerializer
from integrations.datadog.datadog import DataDogWrapper
from integrations.new_relic.new_relic import NewRelicWrapper
from webhooks.webhooks import WebhookEventType, call_organisation_webhooks

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AuditLog)
def call_webhooks(sender, instance, **kwargs):
    data = AuditLogSerializer(instance=instance).data

    if not (instance.project or instance.environment):
        logger.warning("Audit log without project or environment. Not sending webhook.")
        return

    organisation = (
        instance.project.organisation
        if instance.project
        else instance.environment.project.organisation
    )
    call_organisation_webhooks(organisation, data, WebhookEventType.AUDIT_LOG_CREATED)


def _send_audit_log_event_verification(instance, integration):
    if not instance.project:
        logger.warning(
            f"Audit log missing project, not sending data to {integration.get('name')}."
        )
        return

    if not hasattr(instance.project, integration.get("attr")):
        logger.debug(
            f"No datadog integration configured for project {instance.project.id}"
        )
        return

    # Only handle Feature related changes
    if instance.related_object_type not in [
        RelatedObjectType.FEATURE.name,
        RelatedObjectType.FEATURE_STATE.name,
        RelatedObjectType.SEGMENT.name,
    ]:
        logger.debug(
            f"Ignoring none Flag audit event {instance.related_object_type} for {integration.get('name', '').lower()}"
        )
        return

    return getattr(instance.project, integration.get("attr"))


def _track_event_async(instance, integration_client):
    event_data = integration_client.generate_event_data(
        log=instance.log,
        email=instance.author.email if instance.author else "",
        environment_name=instance.environment.name.lower()
        if instance.environment
        else "",
    )

    integration_client.track_event_async(event=event_data)


@receiver(post_save, sender=AuditLog)
def send_audit_log_event_to_datadog(sender, instance, **kwargs):
    integration = {
        "name": "DataDog",
        "attr": "data_dog_config",
    }
    data_dog_config = _send_audit_log_event_verification(instance, integration)

    if not data_dog_config:
        return

    data_dog = DataDogWrapper(
        base_url=data_dog_config.base_url, api_key=data_dog_config.api_key
    )
    _track_event_async(instance, data_dog)


@receiver(post_save, sender=AuditLog)
def send_audit_log_event_to_new_relic(sender, instance, **kwargs):
    integration = {
        "name": "New Relic",
        "attr": "new_relic_config",
    }

    new_relic_config = _send_audit_log_event_verification(instance, integration)
    if not new_relic_config:
        return

    new_relic = NewRelicWrapper(
        base_url=new_relic_config.base_url,
        api_key=new_relic_config.api_key,
        app_id=new_relic_config.app_id,
    )
    _track_event_async(instance, new_relic)


# Intialize the dynamo client globally
dynamo_env_table = None
if settings.ENVIRONMENTS_TABLE_NAME_DYNAMO:
    dynamo_env_table = boto3.resource("dynamodb").Table(
        settings.ENVIRONMENTS_TABLE_NAME_DYNAMO
    )


@receiver(post_save, sender=AuditLog)
def send_env_to_dynamodb(sender, instance, **kwargs):
    environment = instance.environment
    if environment and environment.project.enable_dynamo_db and dynamo_env_table:
        env_dict = build_environment_dict(instance.environment)
        dynamo_env_table.put_item(Item=env_dict)

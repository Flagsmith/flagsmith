from django.db.models.signals import post_save
from django.dispatch import receiver

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from integrations.datadog.datadog import DataDogWrapper
from util.logging import get_logger
from webhooks.webhooks import call_organisation_webhooks, WebhookEventType

logger = get_logger(__name__)


@receiver(post_save, sender=AuditLog)
def call_webhooks(sender, instance, **kwargs):
    data = AuditLogSerializer(instance=instance).data
    if not (instance.project or instance.environment):
        logger.warning('Audit log without project or environment. Not sending webhook.')
        return

    organisation = instance.project.organisation or instance.environment.project.organisation
    call_organisation_webhooks(organisation, data, WebhookEventType.AUDIT_LOG_CREATED)


# pretty sure you can do this and just define multiple receivers but will need to be tested
@receiver(post_save, sender=AuditLog)
def send_audit_log_event_to_datadog(sender, instance, **kwargs):
    if not instance.project:
        logger.warning("Audit log missing project, not sending data to DataDog.")
        return

    data_dog_config = instance.project.data_dog_config
    if not data_dog_config:
        logger.debug("No datadog integration configured for project %s" % instance.project.id)
        return

    data_dog = DataDogWrapper(base_url=data_dog_config.base_url, api_key=data_dog_config.api_key)
    event_data = data_dog.generate_event_data(log=instance.log, email=instance.author.email)
    data_dog.track_event_async(event=event_data)

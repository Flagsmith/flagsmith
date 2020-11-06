from audit.models import AuditLog, RelatedObjectType
from audit.serializers import AuditLogSerializer
from django.db.models.signals import post_save
from django.dispatch import receiver
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

    organisation = instance.project.organisation if instance.project else instance.environment.project.organisation
    call_organisation_webhooks(organisation, data, WebhookEventType.AUDIT_LOG_CREATED)


@receiver(post_save, sender=AuditLog)
def send_audit_log_event_to_datadog(sender, instance, **kwargs):
    if not instance.project:
        logger.warning("Audit log missing project, not sending data to DataDog.")
        return

    if not hasattr(instance.project, 'data_dog_config'):
        logger.debug("No datadog integration configured for project %s" % instance.project.id)
        return

    # Only handle Feature related changes
    if instance.related_object_type not in [RelatedObjectType.FEATURE.name, RelatedObjectType.FEATURE_STATE.name,
                                            RelatedObjectType.SEGMENT.name]:
        logger.debug("Ignoring none Flag audit event %s for datadog" % instance.related_object_type)
        return

    data_dog_config = instance.project.data_dog_config
    data_dog = DataDogWrapper(base_url=data_dog_config.base_url, api_key=data_dog_config.api_key)
    event_data = data_dog.generate_event_data(log=instance.log,
                                              email=instance.author.email if instance.author else '',
                                              environment_name=instance.environment.name.lower()
                                              if instance.environment else '')

    data_dog.track_event_async(event=event_data)

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from webhooks.webhooks import call_organisation_webhooks, WebhookEventType

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@receiver(post_save, sender=AuditLog)
def call_webhooks(sender, instance, **kwargs):
    data = AuditLogSerializer(instance=instance).data
    if not (instance.project or instance.environment):
        logger.warning('Audit log without project or environment. Not sending webhook.')
    organisation = instance.project.organisation or instance.environment.project.organisation
    call_organisation_webhooks(organisation, data, WebhookEventType.AUDIT_LOG_CREATED)

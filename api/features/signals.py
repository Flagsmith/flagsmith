import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from simple_history.signals import post_create_historical_record

from audit.models import (
    FEATURE_SEGMENT_UPDATED_MESSAGE,
    AuditLog,
    RelatedObjectType,
)

# noinspection PyUnresolvedReferences
from .models import (
    FeatureState,
    HistoricalFeatureSegment,
    HistoricalFeatureState,
)
from .tasks import trigger_feature_state_change_webhooks

logger = logging.getLogger(__name__)


@receiver(post_create_historical_record, sender=HistoricalFeatureSegment)
def create_feature_segment_audit_log(
    instance, history_user, history_instance, **kwargs
):
    # due to referential integrity issues that come from cascade deletes, we skip creating
    # audit logs for deleted feature segments for now
    # TODO: handle audit log in middleware instead
    project = None if history_instance.history_type == "-" else instance.feature.project

    message = FEATURE_SEGMENT_UPDATED_MESSAGE % (
        instance.feature.name,
        instance.environment.name,
    )
    AuditLog.create_record(
        obj=instance.feature,
        obj_type=RelatedObjectType.FEATURE,
        log_message=message,
        author=history_user,
        project=project,
    )


@receiver(post_save, sender=FeatureState)
def trigger_feature_state_change_webhooks_signal(instance, **kwargs):
    trigger_feature_state_change_webhooks(instance)

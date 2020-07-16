from django.dispatch import receiver
from simple_history.signals import post_create_historical_record

from audit.models import AuditLog, RelatedObjectType, FEATURE_SEGMENT_UPDATED_MESSAGE
from projects.models import Project
from util.logging import get_logger
# noinspection PyUnresolvedReferences
from .models import HistoricalFeatureSegment

logger = get_logger(__name__)


@receiver(post_create_historical_record, sender=HistoricalFeatureSegment)
def create_feature_segment_audit_log(instance, history_user, history_instance, **kwargs):
    # check if the signal has been triggered by the feature segment being deleted
    deleted = history_instance.history_type == "-"

    # if the feature segment has been deleted, this could have been from a cascade delete. We need to verify that
    # the project still exists.
    project = instance.feature.project
    if deleted and not Project.objects.filter(id=project.id).exists():
        project = None

    message = FEATURE_SEGMENT_UPDATED_MESSAGE % (instance.feature.name, instance.environment.name)
    AuditLog.create_record(
        obj=instance.feature,
        obj_type=RelatedObjectType.FEATURE,
        log_message=message,
        author=history_user,
        project=project
    )

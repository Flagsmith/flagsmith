import enum

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from projects.models import Project

FEATURE_CREATED_MESSAGE = "New Flag / Remote Config created: %s"
FEATURE_UPDATED_MESSAGE = "Flag / Remote Config updated: %s"
SEGMENT_CREATED_MESSAGE = "New Segment created: %s"
SEGMENT_UPDATED_MESSAGE = "Segment updated: %s"
FEATURE_SEGMENT_UPDATED_MESSAGE = "Segment rules updated for flag: %s"
ENVIRONMENT_CREATED_MESSAGE = "New Environment created: %s"
ENVIRONMENT_UPDATED_MESSAGE = "Environment updated: %s"
FEATURE_STATE_UPDATED_MESSAGE = "Flag state / Remote Config value updated for feature: %s"


class RelatedObjectType(enum.Enum):
    FEATURE = "Feature"
    FEATURE_STATE = "Feature state"
    SEGMENT = "Segment"
    ENVIRONMENT = "Environment"


RELATED_OBJECT_TYPES = ((tag.name, tag.value) for tag in RelatedObjectType)


@python_2_unicode_compatible
class AuditLog(models.Model):
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    project = models.ForeignKey(Project, related_name='audit_logs', null=True)
    environment = models.ForeignKey(
        'environments.Environment', related_name='audit_logs', null=True)
    log = models.TextField()
    author = models.ForeignKey(
        'users.FFAdminUser', related_name='audit_logs', null=True, blank=True)
    related_object_id = models.IntegerField(null=True)
    related_object_type = models.CharField(max_length=20, null=True)

    class Meta:
        verbose_name_plural = "Audit Logs"
        ordering = ('-created_date',)

    def __str__(self):
        return "Audit Log %s" % self.id

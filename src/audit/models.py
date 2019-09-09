import enum

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

FEATURE_CREATED_MESSAGE = "New Flag / Remote Config created"
FEATURE_UPDATED_MESSAGE = "Flag / Remove Config updated"


class RelatedObjectType(enum.Enum):
    FEATURE = "Feature"
    FEATURE_STATE = "Feature state"
    SEGMENT = "Segment"
    ENVIRONMENT = "Environment"


RELATED_OBJECT_TYPES = ((tag.name, tag.value) for tag in RelatedObjectType)


@python_2_unicode_compatible
class AuditLog(models.Model):
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    environment = models.ForeignKey(
        'environments.Environment', related_name='audit_logs', null=True)
    log = models.TextField()
    author = models.ForeignKey(
        'users.FFAdminUser', related_name='audit_logs', null=True, blank=True)
    related_object_id = models.IntegerField(null=True)
    related_object_type = models.CharField(max_length=20, null=True)

    class Meta:
        verbose_name_plural = "Audit Logs"

    def __str__(self):
        return "Audit Log %s" % self.id

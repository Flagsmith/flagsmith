import enum

from django.db import models

from projects.models import Project

FEATURE_CREATED_MESSAGE = "New Flag / Remote Config created: %s"
FEATURE_UPDATED_MESSAGE = "Flag / Remote Config updated: %s"
SEGMENT_CREATED_MESSAGE = "New Segment created: %s"
SEGMENT_UPDATED_MESSAGE = "Segment updated: %s"
FEATURE_SEGMENT_UPDATED_MESSAGE = "Segment rules updated for flag: %s in environment: %s"
ENVIRONMENT_CREATED_MESSAGE = "New Environment created: %s"
ENVIRONMENT_UPDATED_MESSAGE = "Environment updated: %s"
FEATURE_STATE_UPDATED_MESSAGE = "Flag state / Remote Config value updated for feature: %s"
IDENTITY_FEATURE_STATE_UPDATED_MESSAGE = "Flag state / Remote config value updated for feature '%s' and identity '%s'"
IDENTITY_FEATURE_STATE_DELETED_MESSAGE = "Flag state / Remote config value deleted for feature '%s' and identity '%s'"


class RelatedObjectType(enum.Enum):
    FEATURE = "Feature"
    FEATURE_STATE = "Feature state"
    SEGMENT = "Segment"
    ENVIRONMENT = "Environment"


RELATED_OBJECT_TYPES = ((tag.name, tag.value) for tag in RelatedObjectType)


class AuditLog(models.Model):
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    project = models.ForeignKey(Project, related_name='audit_logs', null=True, on_delete=models.SET_NULL)
    environment = models.ForeignKey(
        'environments.Environment', related_name='audit_logs', null=True, on_delete=models.SET_NULL)
    log = models.TextField()
    author = models.ForeignKey(
        'users.FFAdminUser', related_name='audit_logs', null=True, blank=True, on_delete=models.SET_NULL)
    related_object_id = models.IntegerField(null=True)
    related_object_type = models.CharField(max_length=20, null=True)

    class Meta:
        verbose_name_plural = "Audit Logs"
        ordering = ('-created_date',)

    def __str__(self):
        return "Audit Log %s" % self.id

    @classmethod
    def create_record(cls, obj, obj_type, log_message, author, project=None, environment=None):
        cls.objects.create(
            related_object_id=obj.id,
            related_object_type=obj_type.name,
            log=log_message,
            author=author,
            project=project,
            environment=environment
        )


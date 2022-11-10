import enum

from django.db import models
from django_lifecycle import AFTER_SAVE, LifecycleModel, hook

from api_keys.models import MasterAPIKey
from projects.models import Project

FEATURE_CREATED_MESSAGE = "New Flag / Remote Config created: %s"
FEATURE_DELETED_MESSAGE = "Flag / Remote Config Deleted: %s"
FEATURE_UPDATED_MESSAGE = "Flag / Remote Config updated: %s"
SEGMENT_CREATED_MESSAGE = "New Segment created: %s"
SEGMENT_UPDATED_MESSAGE = "Segment updated: %s"
FEATURE_SEGMENT_UPDATED_MESSAGE = (
    "Segment rules updated for flag: %s in environment: %s"
)
ENVIRONMENT_CREATED_MESSAGE = "New Environment created: %s"
ENVIRONMENT_UPDATED_MESSAGE = "Environment updated: %s"
FEATURE_STATE_UPDATED_MESSAGE = (
    "Flag state / Remote Config value updated for feature: %s"
)
FEATURE_STATE_WENT_LIVE_MESSAGE = (
    "Scheduled change to Flag state / Remote config value went live for feature: %s by"
    " Change Request: %s"
)

IDENTITY_FEATURE_STATE_UPDATED_MESSAGE = (
    "Flag state / Remote config value updated for feature '%s' and identity '%s'"
)
SEGMENT_FEATURE_STATE_UPDATED_MESSAGE = (
    "Flag state / Remote config value updated for feature '%s' and segment '%s'"
)
IDENTITY_FEATURE_STATE_DELETED_MESSAGE = (
    "Flag state / Remote config value deleted for feature '%s' and identity '%s'"
)
SEGMENT_FEATURE_STATE_DELETED_MESSAGE = (
    "Flag state / Remote config value deleted for feature '%s' and segment '%s'"
)

CHANGE_REQUEST_CREATED_MESSAGE = "Change Request: %s created"
CHANGE_REQUEST_APPROVED_MESSAGE = "Change Request: %s approved"
CHANGE_REQUEST_COMMITTED_MESSAGE = "Change Request: %s committed"


class RelatedObjectType(enum.Enum):
    FEATURE = "Feature"
    FEATURE_STATE = "Feature state"
    SEGMENT = "Segment"
    ENVIRONMENT = "Environment"
    CHANGE_REQUEST = "Change request"


RELATED_OBJECT_TYPES = ((tag.name, tag.value) for tag in RelatedObjectType)


class AuditLog(LifecycleModel):
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)
    project = models.ForeignKey(
        Project, related_name="audit_logs", null=True, on_delete=models.SET_NULL
    )
    environment = models.ForeignKey(
        "environments.Environment",
        related_name="audit_logs",
        null=True,
        on_delete=models.SET_NULL,
    )
    log = models.TextField()
    author = models.ForeignKey(
        "users.FFAdminUser",
        related_name="audit_logs",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    master_api_key = models.ForeignKey(
        MasterAPIKey,
        related_name="audit_logs",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    related_object_id = models.IntegerField(null=True)
    related_object_type = models.CharField(max_length=20, null=True)

    skip_signals = models.CharField(
        null=True,
        blank=True,
        help_text="comma separated list of signal functions to skip",
        max_length=500,
    )
    is_system_event = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Audit Logs"
        ordering = ("-created_date",)

    def __str__(self):
        return "Audit Log %s" % self.id

    @hook(AFTER_SAVE)
    def update_environments_updated_at(self):
        if self.related_object_type == RelatedObjectType.CHANGE_REQUEST.name:
            return

        if self.environment:
            self.environment.updated_at = self.created_date
            self.environment.save()
        else:
            self.project.environments.update(updated_at=self.created_date)

    @classmethod
    def create_record(
        cls,
        obj,
        obj_type,
        log_message,
        author,
        project=None,
        environment=None,
        persist=True,
    ):
        record = cls(
            related_object_id=obj.id,
            related_object_type=obj_type.name,
            log=log_message,
            author=author,
            project=project,
            environment=environment,
        )
        if persist:
            record.save()
        return record

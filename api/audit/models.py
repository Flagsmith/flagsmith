import typing
from importlib import import_module

from django.db import models
from django.db.models import Model
from django_lifecycle import AFTER_SAVE, LifecycleModel, hook

from api_keys.models import MasterAPIKey
from audit.related_object_type import RelatedObjectType
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


RELATED_OBJECT_TYPES = ((tag.name, tag.value) for tag in RelatedObjectType)


class AuditLog(LifecycleModel):
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)

    project = models.ForeignKey(
        Project, related_name="audit_logs", null=True, on_delete=models.DO_NOTHING
    )
    environment = models.ForeignKey(
        "environments.Environment",
        related_name="audit_logs",
        null=True,
        on_delete=models.DO_NOTHING,
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

    history_record_id = models.IntegerField(blank=True, null=True)
    history_record_class_path = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Audit Logs"
        ordering = ("-created_date",)

    @property
    def history_record(self):
        klass = self.get_history_record_model_class(self.history_record_class_path)
        return klass.objects.get(id=self.history_record_id)

    @staticmethod
    def get_history_record_model_class(
        history_record_class_path: str,
    ) -> typing.Type[Model]:
        module_path, class_name = history_record_class_path.rsplit(".", maxsplit=1)
        module = import_module(module_path)
        return getattr(module, class_name)

    @hook(AFTER_SAVE)
    def update_environments_updated_at(self):
        # Don't update the environments updated_at if the audit log
        # is of CHANGE_REQUEST type (since they directly don't (directly)
        # impact value of a given feature in an environment) or ENVIRONMENT
        # since the environment itself has no impact on the feature states
        # within it
        if self.related_object_type in (
            RelatedObjectType.CHANGE_REQUEST.name,
            RelatedObjectType.ENVIRONMENT.name,
        ):
            return

        if self.environment:
            self.environment.updated_at = self.created_date
            self.environment.save()
        else:
            self.project.environments.update(updated_at=self.created_date)

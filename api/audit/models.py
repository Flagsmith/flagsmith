import typing
from importlib import import_module

from django.db import models
from django.db.models import Model, Q
from django_lifecycle import AFTER_SAVE, BEFORE_CREATE, LifecycleModel, hook

from api_keys.models import MasterAPIKey
from audit.related_object_type import RelatedObjectType
from projects.models import Project
from sse import (
    send_environment_update_message_for_environment,
    send_environment_update_message_for_project,
)

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
    related_object_uuid = models.CharField(max_length=36, null=True)

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

    @property
    def can_related_object_type_change_feature_value_for_sdk(self) -> bool:
        # Returns true if the audit log have an object type that can change the
        # feature value for the sdk endpoints
        return self.related_object_type != RelatedObjectType.CHANGE_REQUEST.name

    @hook(AFTER_SAVE)
    def update_environments_updated_at(self):
        # Don't update the environments updated_at if the audit log
        # can not change the value of a feature for sdk
        if not self.can_related_object_type_change_feature_value_for_sdk:
            return

        environments_filter = Q()
        if self.environment_id:
            environments_filter = Q(id=self.environment_id)

        # Use a queryset to perform update to prevent signals being called at this point.
        # Since we're re-saving the environment, we don't want to duplicate signals.
        self.project.environments.filter(environments_filter).update(
            updated_at=self.created_date
        )

        if self.environment_id:
            environment = self.environment
            # update manually to save a db call
            environment.updated_at = self.created_date
            send_environment_update_message_for_environment(environment)
        else:
            send_environment_update_message_for_project(self.project)

    @hook(BEFORE_CREATE)
    def add_project(self):
        if self.environment and self.project is None:
            self.project = self.environment.project

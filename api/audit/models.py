import typing
from importlib import import_module

from django.db import models
from django.db.models import Model, Q
from django_lifecycle import (
    AFTER_CREATE,
    BEFORE_CREATE,
    LifecycleModel,
    hook,
    priority,
)

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

    skip_signals_and_hooks = models.CharField(
        null=True,
        blank=True,
        help_text="comma separated list of signal/hooks functions/methods to skip",
        max_length=500,
        db_column="skip_signals",
    )
    is_system_event = models.BooleanField(default=False)

    history_record_id = models.IntegerField(blank=True, null=True)
    history_record_class_path = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        verbose_name_plural = "Audit Logs"
        ordering = ("-created_date",)

    @property
    def environment_document_updated(self) -> bool:
        if self.related_object_type == RelatedObjectType.CHANGE_REQUEST.name:
            return False
        skip_signals_and_hooks = (
            self.skip_signals_and_hooks.split(",")
            if self.skip_signals_and_hooks
            else []
        )
        return "send_environments_to_dynamodb" not in skip_signals_and_hooks

    @property
    def history_record(self):
        klass = self.get_history_record_model_class(self.history_record_class_path)
        return klass.objects.get(id=self.history_record_id)

    @property
    def environment_name(self) -> str:
        return getattr(self.environment, "name", "unknown")

    @property
    def author_identifier(self) -> str:
        return getattr(self.author, "email", "system")

    @staticmethod
    def get_history_record_model_class(
        history_record_class_path: str,
    ) -> typing.Type[Model]:
        module_path, class_name = history_record_class_path.rsplit(".", maxsplit=1)
        module = import_module(module_path)
        return getattr(module, class_name)

    @hook(BEFORE_CREATE)
    def add_project(self):
        if self.environment and self.project is None:
            self.project = self.environment.project

    @hook(
        AFTER_CREATE,
        priority=priority.HIGHEST_PRIORITY,
        when="environment_document_updated",
        is_now=True,
    )
    def process_environment_update(self):
        self.send_environments_to_dynamodb()
        self.send_environment_update_message()

    def update_environments_updated_at(self):
        environments_filter = Q()
        if self.environment_id:
            environments_filter = Q(id=self.environment_id)

        # Use a queryset to perform update to prevent signals being called at this point.
        # Since we're re-saving the environment, we don't want to duplicate signals.
        self.project.environments.filter(environments_filter).update(
            updated_at=self.created_date
        )

    def send_environments_to_dynamodb(self):
        from environments.models import Environment

        Environment.write_environments_to_dynamodb(
            environment_id=self.environment_id, project_id=self.project_id
        )

    def send_environment_update_message(self):
        if self.environment_id:
            environment = self.environment
            # Because we updated the environment `updated_at` in the previous hook in bulk
            # update it manually here to save a `refresh_from_db` call
            environment.updated_at = self.created_date
            send_environment_update_message_for_environment(environment)
        else:
            send_environment_update_message_for_project(self.project)

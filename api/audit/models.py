import typing
from functools import cached_property
from importlib import import_module

from django.db import models
from django.db.models import Model, Q
from django.utils import timezone
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

RELATED_OBJECT_TYPES = ((tag.name, tag.value) for tag in RelatedObjectType)


class AuditLog(LifecycleModel):
    created_date = models.DateTimeField("DateCreated")

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

    @cached_property
    def history_record(self) -> typing.Optional[Model]:
        if not (self.history_record_class_path and self.history_record_id):
            # There are still AuditLog records that will not have this detail
            # for example, audit log records which are created when segment
            # override priorities are changed.
            return

        klass = self.get_history_record_model_class(self.history_record_class_path)
        return klass.objects.filter(history_id=self.history_record_id).first()

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

    @hook(BEFORE_CREATE)
    def add_created_date(self) -> None:
        if not self.created_date:
            self.created_date = timezone.now()

    @hook(
        AFTER_CREATE,
        priority=priority.HIGHEST_PRIORITY,
        when="environment_document_updated",
        is_now=True,
    )
    def process_environment_update(self):
        from environments.models import Environment
        from environments.tasks import process_environment_update

        environments_filter = Q()
        if self.environment_id:
            environments_filter = Q(id=self.environment_id)

        environment_ids = self.project.environments.filter(
            environments_filter
        ).values_list("id", flat=True)

        # Update environment individually to avoid deadlock
        for environment_id in environment_ids:
            Environment.objects.filter(id=environment_id).update(
                updated_at=self.created_date
            )

        process_environment_update.delay(args=(self.id,))

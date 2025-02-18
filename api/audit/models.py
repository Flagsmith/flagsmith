import typing
from functools import cached_property
from importlib import import_module

from django.db import models
from django.db.models import Model, Q
from django.utils import timezone
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_CREATE,
    BEFORE_CREATE,
    LifecycleModel,
    hook,
    priority,
)

from api_keys.models import MasterAPIKey
from audit.related_object_type import RelatedObjectType
from projects.models import Project

if typing.TYPE_CHECKING:
    from organisations.models import Organisation

RELATED_OBJECT_TYPES = ((tag.name, tag.value) for tag in RelatedObjectType)


class AuditLog(LifecycleModel):  # type: ignore[misc]
    created_date = models.DateTimeField("DateCreated")  # type: ignore[var-annotated]

    project = models.ForeignKey(  # type: ignore[var-annotated]
        Project, related_name="audit_logs", null=True, on_delete=models.DO_NOTHING
    )
    environment = models.ForeignKey(  # type: ignore[var-annotated]
        "environments.Environment",
        related_name="audit_logs",
        null=True,
        on_delete=models.DO_NOTHING,
    )

    log = models.TextField()  # type: ignore[var-annotated]
    author = models.ForeignKey(  # type: ignore[var-annotated]
        "users.FFAdminUser",
        related_name="audit_logs",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    master_api_key = models.ForeignKey(  # type: ignore[var-annotated]
        MasterAPIKey,
        related_name="audit_logs",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    related_object_id = models.IntegerField(null=True)  # type: ignore[var-annotated]
    related_object_type = models.CharField(max_length=20, null=True)  # type: ignore[var-annotated]
    related_object_uuid = models.CharField(max_length=36, null=True)  # type: ignore[var-annotated]

    skip_signals_and_hooks = models.CharField(  # type: ignore[var-annotated]
        null=True,
        blank=True,
        help_text="comma separated list of signal/hooks functions/methods to skip",
        max_length=500,
        db_column="skip_signals",
    )
    is_system_event = models.BooleanField(default=False)  # type: ignore[var-annotated]

    history_record_id = models.IntegerField(blank=True, null=True)  # type: ignore[var-annotated]
    history_record_class_path = models.CharField(max_length=200, blank=True, null=True)  # type: ignore[var-annotated]

    class Meta:
        verbose_name_plural = "Audit Logs"
        ordering = ("-created_date",)

    @property
    def organisation(self) -> "Organisation | None":
        # TODO properly implement organisation relation
        # maybe the relation list should not be _that_ exhaustive...
        for relation in (
            "project",
            "environment",
            "author",
            "master_api_key",
            "history_record",
        ):
            if hasattr(related_instance := getattr(self, relation), "organisation"):
                return related_instance.organisation  # type: ignore[no-any-return]
        return None

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
            return  # type: ignore[return-value]

        klass = self.get_history_record_model_class(self.history_record_class_path)
        return klass.objects.filter(history_id=self.history_record_id).first()  # type: ignore[attr-defined,no-any-return]  # noqa: E501

    @property
    def project_name(self) -> str:
        return getattr(self.project, "name", "unknown")

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
        return getattr(module, class_name)  # type: ignore[no-any-return]

    @hook(BEFORE_CREATE)
    def add_project(self):  # type: ignore[no-untyped-def]
        if self.environment and self.project is None:
            self.project = self.environment.project

    @hook(BEFORE_CREATE)  # type: ignore[misc]
    def add_created_date(self) -> None:
        if not self.created_date:
            self.created_date = timezone.now()

    @hook(  # type: ignore[misc]
        AFTER_CREATE,
        priority=priority.HIGHEST_PRIORITY,
        when="environment_document_updated",
        is_now=True,
    )
    def process_environment_update(self) -> None:
        if not self.project:
            return

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

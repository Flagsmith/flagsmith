import typing

from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone

from audit.constants import (
    RELEASE_PIPELINE_CREATED_MESSAGE,
    RELEASE_PIPELINE_DELETED_MESSAGE,
    RELEASE_PIPELINE_PUBLISHED_MESSAGE,
)
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from core.models import (
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory,
)
from features.release_pipelines.core.constants import MAX_PIPELINE_STAGES
from features.release_pipelines.core.exceptions import InvalidPipelineStateError
from projects.models import Project
from users.models import FFAdminUser


class StageTriggerType(models.TextChoices):
    ON_ENTER = "ON_ENTER", "Trigger when flag enters stage"
    WAIT_FOR = "WAIT_FOR", "Trigger after waiting for x amount of time"


class StageActionType(models.TextChoices):
    TOGGLE_FEATURE = "TOGGLE_FEATURE", "Enable/Disable Feature for the environment"
    UPDATE_FEATURE_VALUE = (
        "UPDATE_FEATURE_VALUE",
        "Update Feature Value for the environment",
    )
    TOGGLE_FEATURE_FOR_SEGMENT = (
        "TOGGLE_FEATURE_FOR_SEGMENT",
        "Enable/Disable Feature for a specific segment",
    )
    UPDATE_FEATURE_VALUE_FOR_SEGMENT = (
        "UPDATE_FEATURE_VALUE_FOR_SEGMENT",
        "Update Feature Value for a specific segment",
    )


class ReleasePipeline(
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(),  # type: ignore[misc]
):
    history_record_class_path = (
        "features.release_pipelines.core.models.HistoricalReleasePipeline"
    )
    related_object_type = RelatedObjectType.RELEASE_PIPELINE

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    project = models.ForeignKey(
        "projects.Project", related_name="release_pipelines", on_delete=models.CASCADE
    )

    published_at = models.DateTimeField(blank=True, null=True)
    published_by = models.ForeignKey(
        FFAdminUser,
        related_name="published_release_pipelines",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def publish(self, published_by: FFAdminUser) -> None:
        if self.published_at is not None:
            raise InvalidPipelineStateError("Pipeline is already published.")
        self.published_at = timezone.now()
        self.published_by = published_by
        self.save()
        self._create_pipeline_published_audit_log()

    def get_first_stage(self) -> "PipelineStage | None":
        return self.stages.order_by("order").first()

    def get_last_stage(self) -> "PipelineStage | None":
        return self.stages.order_by("-order").first()

    def get_create_log_message(
        self, history_instance: "ReleasePipeline"
    ) -> typing.Optional[str]:
        return RELEASE_PIPELINE_CREATED_MESSAGE % self.name

    def get_delete_log_message(
        self, history_instance: "ReleasePipeline"
    ) -> typing.Optional[str]:
        return RELEASE_PIPELINE_DELETED_MESSAGE % self.name

    def _get_project(self) -> Project:
        return self.project

    def _create_pipeline_published_audit_log(self) -> None:
        AuditLog.objects.create(
            related_object_id=self.id,
            related_object_type=RelatedObjectType.RELEASE_PIPELINE.name,
            project=self._get_project(),
            log=RELEASE_PIPELINE_PUBLISHED_MESSAGE % self.name,
            author=self.published_by,
        )


class PipelineStage(models.Model):
    name = models.CharField(max_length=255)
    pipeline = models.ForeignKey(
        "ReleasePipeline", related_name="stages", on_delete=models.CASCADE
    )
    order = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(MAX_PIPELINE_STAGES)]
    )

    environment = models.ForeignKey(
        "environments.Environment",
        related_name="pipeline_stages",
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["pipeline", "order"], name="unique_pipeline_stage_order"
            )
        ]

    def get_next_stage(self) -> "PipelineStage | None":
        return (
            PipelineStage.objects.filter(pipeline=self.pipeline, order__gt=self.order)
            .order_by("order")
            .first()
        )


class PipelineStageTrigger(models.Model):
    trigger_type = models.CharField(
        max_length=50,
        choices=StageTriggerType.choices,
        default=StageTriggerType.ON_ENTER,
    )
    trigger_body = models.JSONField(null=True)

    stage = models.OneToOneField(
        PipelineStage,
        related_name="trigger",
        on_delete=models.CASCADE,
    )


class PipelineStageAction(models.Model):
    action_type = models.CharField(
        max_length=50,
        choices=StageActionType.choices,
        default=StageActionType.TOGGLE_FEATURE,
    )
    action_body = models.JSONField(null=True)
    stage = models.ForeignKey(
        PipelineStage,
        related_name="actions",
        on_delete=models.CASCADE,
    )

import typing
from datetime import datetime

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q, QuerySet
from django.utils import timezone
from django_lifecycle import (  # type: ignore[import-untyped]
    BEFORE_CREATE,
    LifecycleModelMixin,
    hook,
)

from audit.constants import (
    RELEASE_PIPELINE_CREATED_MESSAGE,
    RELEASE_PIPELINE_DELETED_MESSAGE,
)
from audit.related_object_type import RelatedObjectType
from core.models import (
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory,
)
from features.release_pipelines.core.constants import MAX_PIPELINE_STAGES
from features.release_pipelines.core.exceptions import InvalidPipelineStateError
from features.versioning.models import EnvironmentFeatureVersion
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
    PHASED_ROLLOUT = ("PHASED_ROLLOUT", "Create Phased Rollout")


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

    def unpublish(self) -> None:
        if self.published_at is None:
            raise InvalidPipelineStateError("Pipeline is not published.")
        self.published_at = None
        self.published_by = None
        self.save()

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

    def get_feature_versions_in_pipeline_qs(
        self,
    ) -> QuerySet[EnvironmentFeatureVersion]:
        base_qs = EnvironmentFeatureVersion.objects.filter(
            pipeline_stage__pipeline=self
        )
        phased_rollout_action_filter = Q(phased_rollout_state__isnull=False) & Q(
            phased_rollout_state__is_rollout_complete=False
        )
        all_other_action_filters = Q(published_at__isnull=True)
        qs: QuerySet[EnvironmentFeatureVersion] = base_qs.filter(
            all_other_action_filters | phased_rollout_action_filter
        )
        return qs

    def has_feature_in_flight(self) -> bool:
        has_feature_in_flight: bool = (
            self.get_feature_versions_in_pipeline_qs().exists()
        )
        return has_feature_in_flight

    def _get_project(self) -> Project:
        return self.project


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

    def get_phased_rollout_action(self) -> "PipelineStageAction | None":
        return self.actions.filter(action_type=StageActionType.PHASED_ROLLOUT).first()

    def get_in_stage_feature_versions_qs(self) -> QuerySet[EnvironmentFeatureVersion]:
        phased_rollout_action_filter = Q(
            phased_rollout_state__isnull=False,
            phased_rollout_state__is_rollout_complete=False,
        )
        all_other_action_filters = Q(
            published_at__isnull=True, phased_rollout_state__isnull=True
        )

        return self.environment_feature_versions.filter(
            all_other_action_filters | phased_rollout_action_filter
        )

    def get_completed_feature_versions_qs(
        self, completed_after: datetime = timezone.now()
    ) -> QuerySet[EnvironmentFeatureVersion]:
        phased_rollout_action_filter = Q(
            phased_rollout_state__is_rollout_complete=True,
            phased_rollout_state__last_updated_at__gte=completed_after,
        )
        all_other_action_filters = Q(
            published_at__gte=completed_after, phased_rollout_state__isnull=True
        )

        return self.environment_feature_versions.filter(
            all_other_action_filters | phased_rollout_action_filter
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


class PhasedRolloutState(LifecycleModelMixin, models.Model):  # type: ignore[misc]
    initial_split = models.FloatField(
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(100.0),
        ]
    )
    increase_by = models.FloatField(
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(100.0),
        ]
    )
    increase_every = models.DurationField()
    current_split = models.FloatField(
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(100.0),
        ]
    )
    rollout_segment = models.OneToOneField(
        "segments.Segment",
        related_name="phased_rollout_state",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_rollout_complete = models.BooleanField(default=False)
    last_updated_at = models.DateTimeField(auto_now=True)

    @hook(BEFORE_CREATE)  # type: ignore[misc]
    def set_initial_split(self) -> None:
        if self.current_split is None:
            self.current_split = self.initial_split

    def increase_split(self) -> float:
        self.current_split = min(self.current_split + self.increase_by, 100.0)
        self.save()

        # Update the segment value
        condition = self.rollout_segment.rules.first().conditions.first()  # type: ignore[union-attr]
        assert condition
        condition.value = str(self.current_split)
        condition.save()
        return self.current_split

    def complete_rollout(self) -> None:
        assert self.rollout_segment is not None
        self.rollout_segment.delete()
        self.is_rollout_complete = True
        self.save()

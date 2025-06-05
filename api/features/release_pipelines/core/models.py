import json
from typing import Any

from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone

from features.release_pipelines.core.exceptions import InvalidPipelineStateError
from features.versioning.models import EnvironmentFeatureVersion
from users.models import FFAdminUser

MAX_PIPELINE_STAGES = 30


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


class ReleasePipeline(models.Model):
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

    def get_first_stage(self) -> "PipelineStage | None":
        return self.stages.filter(order=0).get()


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
        return PipelineStage.objects.filter(
            pipeline=self.pipeline, order=self.order + 1
        ).first()

    def get_feature_states_to_create_json_str(self, feature_id: int) -> str:
        return json.dumps("")


class PipelineStageTrigger(models.Model):
    trigger_type = models.CharField(
        max_length=50,
        choices=StageTriggerType.choices,
        default=StageTriggerType.ON_ENTER,
    )
    trigger_body = models.JSONField(null=True)  # Json field?

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
    action_body = models.JSONField(null=True)  # Json field?
    stage = models.ForeignKey(
        PipelineStage,
        related_name="actions",
        on_delete=models.CASCADE,
    )

    def get_feature_state_to_update(
        self, feature_version: EnvironmentFeatureVersion
    ) -> dict[str, Any] | None:
        action_body = json.loads(self.action_body or "{}")
        if self.action_type == StageActionType.TOGGLE_FEATURE:
            return {
                "feature": feature_version.feature_id,
                "enabled": action_body["enabled"],
                "feature_segment": None,
            }
        if self.action_type == StageActionType.TOGGLE_FEATURE_FOR_SEGMENT:
            feature_segment_id = None
            if fs := feature_version.feature_states.filter(
                feature_segment__segment=action_body["segment_id"]
            ).first():
                feature_segment_id = fs.feature_segment.id

            return {
                "feature": feature_version.feature_id,
                "enabled": action_body["enabled"],
                "feature_segment": {
                    "segment": action_body["segment_id"],
                    "id": feature_segment_id,
                },
            }
        if self.action_type == StageActionType.UPDATE_FEATURE_VALUE:
            return {
                "feature": feature_version.feature_id,
                "feature_state_value": {
                    "boolean_value": action_body.get("boolean_value"),
                    "string_value": action_body.get("string_value"),
                    "integer_value": action_body.get("integer_value"),
                    "type": action_body.get("type"),
                },
                "feature_segment": None,
            }
        if self.action_type == StageActionType.UPDATE_FEATURE_VALUE_FOR_SEGMENT:
            feature_segment_id = None
            if fs := feature_version.feature_states.filter(
                feature_segment__segment=action_body["segment_id"]
            ).first():
                feature_segment_id = fs.feature_segment.id

            return {
                "feature": feature_version.feature_id,
                "feature_state_value": {
                    "boolean_value": action_body.get("boolean_value"),
                    "string_value": action_body.get("string_value"),
                    "integer_value": action_body.get("integer_value"),
                    "type": action_body.get("type"),
                },
                "feature_segment": {
                    "segment": action_body["segment_id"],
                    "id": feature_segment_id,
                },
            }

        return None

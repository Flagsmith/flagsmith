import json

from django.core.validators import MaxValueValidator
from django.db import models

MAX_PIPELINE_STAGES = 30


class StageTriggerType(models.TextChoices):
    ON_ENTER = "ON_ENTER", "Trigger when flag enters stage"
    WAIT_FOR = "WAIT_FOR", "Trigger after waiting for x amount of time"


TRIGGER_TYPE_SCHEMA: dict[str, dict[str, list[str]]] = {
    StageTriggerType.ON_ENTER: {"required_fields": []},
    StageTriggerType.WAIT_FOR: {
        "required_fields": ["days", "hours", "minutes", "seconds"]
    },
}


class RelesePipelineStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    ACTIVE = "ACTIVE", "Active"
    ARCHIVED = "ARCHIVED", "Archived"


class ReleasePipeline(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    project = models.ForeignKey(
        "projects.Project", related_name="release_pipelines", on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=50,
        choices=RelesePipelineStatus.choices,
        default=RelesePipelineStatus.DRAFT,
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

    def get_feature_states_to_create_json_str(self, feature_id: int) -> str:
        return ""

    def get_feature_states_to_update_json_str(self, feature_id: int) -> str:
        # TODO: Add other action
        fs_to_update = []
        for action in self.actions.all():
            fs_to_update.append(action.get_feature_state_to_update(feature_id))

        return json.dumps(fs_to_update)


class PipelineStageTrigger(models.Model):
    trigger_type = models.CharField(
        max_length=50,
        choices=StageTriggerType.choices,
        default=StageTriggerType.ON_ENTER,
    )
    trigger_body = models.TextField(null=True)  # Json field?

    stage = models.OneToOneField(
        PipelineStage,
        related_name="trigger",
        on_delete=models.CASCADE,
    )


class StageActionType(models.TextChoices):
    TOGGLE_FEATURE = "TOGGLE_FEATURE", "Enable/Disable Feature for the environment"
    TOGGLE_FEATURE_FOR_SEGMENT = (
        "TOGGLE_FEATURE_FOR_SEGMENT",
        "Enable/Disable Feature for a specific segment",
    )


ACTION_TYPE_SCHEMA: dict[str, dict[str, list[str]]] = {
    StageActionType.TOGGLE_FEATURE: {"required_fields": ["enabled"]},
    StageActionType.TOGGLE_FEATURE_FOR_SEGMENT: {
        "required_fields": ["enabled", "segment_id"]
    },
}


class PipelineStageAction(models.Model):
    action_type = models.CharField(
        max_length=50,
        choices=StageActionType.choices,
        default=StageActionType.TOGGLE_FEATURE,
    )
    action_body = models.TextField(null=True)  # Json field?
    stage = models.ForeignKey(
        PipelineStage,
        related_name="actions",
        on_delete=models.CASCADE,
    )

    def get_feature_state_to_update(
        self, feature_id: int
    ) -> dict[str, int | str | bool | None] | None:
        action_body = json.loads(self.action_body or "{}")
        if self.action_type == StageActionType.TOGGLE_FEATURE:
            return {
                "feature": feature_id,
                "enabled": action_body["enabled"],
                "feature_segment": None,
            }
        # TODO: add other action
        return None

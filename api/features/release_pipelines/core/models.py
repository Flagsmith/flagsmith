from django.db import models


class StageTriggerType(models.TextChoices):
    ON_ENTER = "ON_ENTER", "Trigger when flag enters stage"


TRIGGER_TYPE_SCHEMA: dict[str, dict[str, list[str]]] = {
    StageTriggerType.ON_ENTER: {"required_fields": []},
}

trigger_body = {"segment_id": 1, "value": "this value"}


class ReleasePipeline(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(
        "projects.Project", related_name="release_pipelines", on_delete=models.CASCADE
    )


class PipelineStage(models.Model):
    name = models.CharField(max_length=255)
    pipeline = models.ForeignKey(
        "ReleasePipeline", related_name="stages", on_delete=models.CASCADE
    )
    order = models.IntegerField()
    environment = models.ForeignKey(
        "environments.Environment",
        related_name="pipeline_stages",
        on_delete=models.CASCADE,
    )
    # TODO: Impose limit on the number of stages in a pipeline


class PipelineStageTrigger(models.Model):
    trigger_type = models.CharField(
        max_length=50,
        choices=StageTriggerType.choices,
        default=StageTriggerType.ON_ENTER,
    )
    trigger_body = models.TextField(null=True)  # Json field?
    # TODO: maybe one to one?
    stage = models.ForeignKey(
        PipelineStage,
        related_name="triggers",
        on_delete=models.CASCADE,
    )


class StageActionType(models.TextChoices):
    ENABLE_FEATURE = "ENABLE_FEATURE", "Enable Feature for the environment"
    DISABLE_FEATURE = "DISABLE_FEATURE", "Disable Feature for the environment"


ACTION_TYPE_SCHEMA: dict[str, dict[str, list[str]]] = {
    StageActionType.ENABLE_FEATURE: {"required_fields": []},
    StageActionType.DISABLE_FEATURE: {"required_fields": []},
}


class PipelineStageAction(models.Model):
    action_type = models.CharField(
        max_length=50,
        choices=StageActionType.choices,
        default=StageActionType.ENABLE_FEATURE,
    )
    action_body = models.TextField(null=True)  # Json field?
    stage = models.ForeignKey(
        PipelineStage,
        related_name="actions",
        on_delete=models.CASCADE,
    )

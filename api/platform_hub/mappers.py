from __future__ import annotations

from typing import Any

from platform_hub.types import ReleasePipelineStageStatsData


def map_release_pipeline_stage_to_stats_data(
    stage: Any,
) -> ReleasePipelineStageStatsData:
    """Map a PipelineStage instance to a ReleasePipelineStageStatsData dict."""
    features_in_stage: int = stage.get_in_stage_feature_versions_qs().count()
    features_completed: int = stage.get_completed_feature_versions_qs().count()

    return ReleasePipelineStageStatsData(
        stage_name=stage.name,
        environment_name=stage.environment.name,
        order=stage.order,
        features_in_stage=features_in_stage,
        features_completed=features_completed,
        action_description=_build_action_description(stage),
        trigger_description=_build_trigger_description(stage),
    )


def _build_action_description(stage: Any) -> str:
    """Build a human-readable description of the stage's actions."""
    actions = stage.actions.all()
    if not actions:
        return ""
    descriptions: list[str] = []
    for action in actions:
        descriptions.append(action.get_action_type_display())
    return ", ".join(descriptions)


def _build_trigger_description(stage: Any) -> str:
    """Build a human-readable description of the stage's trigger."""
    try:
        trigger = stage.trigger
    except stage.__class__.trigger.RelatedObjectDoesNotExist:
        return ""

    description: str = trigger.get_trigger_type_display()
    if trigger.trigger_body and "wait_for" in trigger.trigger_body:
        description += f" ({trigger.trigger_body['wait_for']})"
    return description

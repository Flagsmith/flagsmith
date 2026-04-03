from typing import Any

from django.utils.formats import get_format

from features.models import FeatureState
from integrations.gitlab.constants import GitLabEventType


def map_feature_states_to_dicts(
    feature_states: list[FeatureState],
    event_type: str,
) -> list[dict[str, Any]]:
    """Map FeatureState objects to dicts suitable for comment generation.

    Used by both GitHub and GitLab integrations.
    """
    result: list[dict[str, Any]] = []

    for feature_state in feature_states:
        feature_state_value = feature_state.get_feature_state_value()
        env_data: dict[str, Any] = {}

        if feature_state_value is not None:
            env_data["feature_state_value"] = feature_state_value

        if event_type != GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
            env_data["environment_name"] = feature_state.environment.name  # type: ignore[union-attr]
            env_data["enabled"] = feature_state.enabled
            env_data["last_updated"] = feature_state.updated_at.strftime(
                get_format("DATETIME_INPUT_FORMATS")[0]
            )
            env_data["environment_api_key"] = (
                feature_state.environment.api_key  # type: ignore[union-attr]
            )

        if (
            hasattr(feature_state, "feature_segment")
            and feature_state.feature_segment is not None
        ):
            env_data["segment_name"] = feature_state.feature_segment.segment.name

        result.append(env_data)

    return result

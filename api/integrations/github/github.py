import logging
import typing

from core.helpers import get_current_site_url
from django.utils.formats import get_format

from features.models import Feature, FeatureState, FeatureStateValue
from integrations.github.constants import (
    DELETED_FEATURE_TEXT,
    DELETED_SEGMENT_OVERRIDE_TEXT,
    FEATURE_ENVIRONMENT_URL,
    FEATURE_TABLE_HEADER,
    FEATURE_TABLE_ROW,
    LINK_FEATURE_TITLE,
    LINK_SEGMENT_TITLE,
    UNLINKED_FEATURE_TEXT,
    UPDATED_FEATURE_TEXT,
)
from webhooks.webhooks import WebhookEventType

from .dataclasses import GithubData
from .models import GithubConfiguration

logger = logging.getLogger(__name__)


def generate_body_comment(
    name: str,
    event_type: str,
    project_id: int,
    feature_id: int,
    feature_states: typing.List[typing.Dict[str, typing.Any]],
    segment_name: str | None = None,
) -> str:

    is_update = event_type == WebhookEventType.FLAG_UPDATED.value
    is_removed = event_type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
    is_segment_override_deleted = (
        event_type == WebhookEventType.SEGMENT_OVERRIDE_DELETED.value
    )

    if event_type == WebhookEventType.FLAG_DELETED.value:
        return DELETED_FEATURE_TEXT % (name)

    if is_removed:
        return UNLINKED_FEATURE_TEXT % (name)

    if is_segment_override_deleted and segment_name is not None:
        return DELETED_SEGMENT_OVERRIDE_TEXT % (segment_name, name)

    result = UPDATED_FEATURE_TEXT % (name) if is_update else LINK_FEATURE_TITLE % (name)
    last_segment_name = ""
    if len(feature_states) > 0 and not feature_states[0].get("segment_name"):
        result += FEATURE_TABLE_HEADER

    for fs in feature_states:
        feature_value = fs.get("feature_state_value")
        tab = "segment-overrides" if fs.get("segment_name") is not None else "value"
        environment_link_url = FEATURE_ENVIRONMENT_URL % (
            get_current_site_url(),
            project_id,
            fs.get("environment_api_key"),
            feature_id,
            tab,
        )
        if (
            fs.get("segment_name") is not None
            and fs["segment_name"] != last_segment_name
        ):
            result += "\n" + LINK_SEGMENT_TITLE % (fs["segment_name"])
            last_segment_name = fs["segment_name"]
            result += FEATURE_TABLE_HEADER
        table_row = FEATURE_TABLE_ROW % (
            fs["environment_name"],
            environment_link_url,
            "✅ Enabled" if fs["enabled"] else "❌ Disabled",
            f"`{feature_value}`" if feature_value else "",
            fs["last_updated"],
        )
        result += table_row

    return result


def check_not_none(value: any) -> bool:
    return value is not None


def generate_data(
    github_configuration: GithubConfiguration,
    feature: Feature,
    type: str,
    feature_states: (
        typing.Union[list[FeatureState], list[FeatureStateValue]] | None
    ) = None,
    url: str | None = None,
    segment_name: str | None = None,
) -> GithubData:
    if feature_states:
        feature_states_list = []
        for feature_state in feature_states:
            feature_state_value = feature_state.get_feature_state_value()
            feature_env_data = {}

            if check_not_none(feature_state_value):
                feature_env_data["feature_state_value"] = feature_state_value

            if type is not WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
                feature_env_data["environment_name"] = feature_state.environment.name
                feature_env_data["enabled"] = feature_state.enabled
                feature_env_data["last_updated"] = feature_state.updated_at.strftime(
                    get_format("DATETIME_INPUT_FORMATS")[0]
                )
                feature_env_data["environment_api_key"] = (
                    feature_state.environment.api_key
                )
            if (
                hasattr(feature_state, "feature_segment")
                and feature_state.feature_segment is not None
            ):
                feature_env_data["segment_name"] = (
                    feature_state.feature_segment.segment.name
                )
            feature_states_list.append(feature_env_data)

    return GithubData(
        feature_id=feature.id,
        feature_name=feature.name,
        installation_id=github_configuration.installation_id,
        type=type,
        url=(
            url
            if type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
            else None
        ),
        feature_states=feature_states_list if feature_states else None,
        project_id=feature.project_id,
        segment_name=segment_name,
    )

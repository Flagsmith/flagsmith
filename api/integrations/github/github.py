import datetime
import logging
import typing
from dataclasses import dataclass

import requests
from core.helpers import get_current_site_url
from django.conf import settings
from django.utils.formats import get_format

from features.models import FeatureState, FeatureStateValue
from integrations.github.client import generate_token
from integrations.github.constants import (
    DELETED_FEATURE_TEXT,
    FEATURE_ENVIRONMENT_URL,
    FEATURE_TABLE_HEADER,
    FEATURE_TABLE_ROW,
    GITHUB_API_URL,
    LINK_FEATURE_TITLE,
    LINK_SEGMENT_TITLE,
    UNLINKED_FEATURE_TEXT,
    UPDATED_FEATURE_TEXT,
)
from integrations.github.models import GithubConfiguration
from webhooks.webhooks import WebhookEventType

logger = logging.getLogger(__name__)


@dataclass
class GithubData:
    installation_id: str
    feature_id: int
    feature_name: str
    type: str
    feature_states: typing.List[dict[str, typing.Any]] | None = None
    url: str | None = None
    project_id: int | None = None

    @classmethod
    def from_dict(cls, data_dict: dict) -> "GithubData":
        return cls(**data_dict)


def post_comment_to_github(
    installation_id: str, owner: str, repo: str, issue: str, body: str
) -> typing.Optional[typing.Dict[str, typing.Any]]:
    try:
        token = generate_token(
            installation_id,
            settings.GITHUB_APP_ID,
        )

        url = f"{GITHUB_API_URL}repos/{owner}/{repo}/issues/{issue}/comments"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {token}",
        }

        payload = {"body": body}
        response = response = requests.post(
            url, json=payload, headers=headers, timeout=10
        )

        return response.json() if response.status_code == 201 else None
    except requests.RequestException as e:
        logger.error(f" {e}")
        return None


def generate_body_comment(
    name: str,
    event_type: str,
    project_id: int,
    feature_id: int,
    feature_states: typing.List[typing.Dict[str, typing.Any]],
) -> str:

    is_update = event_type == WebhookEventType.FLAG_UPDATED.value
    is_removed = event_type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
    delete_text = UNLINKED_FEATURE_TEXT % (name,)

    if event_type == WebhookEventType.FLAG_DELETED.value:
        return DELETED_FEATURE_TEXT % (name,)

    if is_removed:
        return delete_text

    last_updated_string = datetime.datetime.now().strftime(
        get_format("DATETIME_INPUT_FORMATS")[0]
    )

    result = UPDATED_FEATURE_TEXT % (name) if is_update else LINK_FEATURE_TITLE % (name)
    last_segment_name = ""
    if len(feature_states) > 0 and not feature_states[0].get("segment_name"):
        result += FEATURE_TABLE_HEADER

    for v in feature_states:
        feature_value = v.get("feature_state_value")
        tab = "segment-overrides" if v.get("segment_name") is not None else "value"
        environment_link_url = FEATURE_ENVIRONMENT_URL % (
            get_current_site_url(),
            project_id,
            v.get("environment_api_key"),
            feature_id,
            tab,
        )
        if v.get("segment_name") is not None and v["segment_name"] != last_segment_name:
            result += "\n" + LINK_SEGMENT_TITLE % (v["segment_name"])
            last_segment_name = v["segment_name"]
            result += FEATURE_TABLE_HEADER
        table_row = FEATURE_TABLE_ROW % (
            v["environment_name"],
            environment_link_url,
            "✅ Enabled" if v["enabled"] else "❌ Disabled",
            f"`{feature_value}`" if feature_value else "",
            last_updated_string,
        )
        result += table_row

    return result


def check_not_none(value: any) -> bool:
    return value is not None


def generate_data(
    github_configuration: GithubConfiguration,
    feature_id: int,
    feature_name: str,
    type: str,
    feature_states: (
        typing.Union[list[FeatureState], list[FeatureStateValue]] | None
    ) = None,
    url: str | None = None,
    project_id: int | None = None,
) -> GithubData:

    if feature_states:
        feature_states_list = []
        for feature_state in feature_states:
            feature_state_value = feature_state.get_feature_state_value()
            feature_state_value_type = feature_state.get_feature_state_value_type(
                feature_state_value
            )
            feature_env_data = {}
            if check_not_none(feature_state_value):
                feature_env_data["feature_state_value"] = feature_state_value
                feature_env_data["feature_state_value_type"] = feature_state_value_type
            if type is not WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
                feature_env_data["environment_name"] = feature_state.environment.name
                feature_env_data["enabled"] = feature_state.enabled
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
        feature_id=feature_id,
        feature_name=feature_name,
        installation_id=github_configuration.installation_id,
        type=type,
        url=(
            url
            if type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
            else None
        ),
        feature_states=feature_states_list if feature_states else None,
        project_id=project_id,
    )

import datetime
import logging
import typing
from dataclasses import dataclass

import requests
from django.conf import settings

from features.models import FeatureState, FeatureStateValue
from integrations.github.client import generate_token
from integrations.github.constants import (
    GITHUB_API_URL,
    LAST_UPDATED_FEATURE_TEXT,
    LINK_FEATURE_TEXT,
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
    feature_states: typing.List[dict[str, typing.Any]] = None
    url: str = None

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

        return response.json() if response.status_code == 200 else None
    except requests.RequestException as e:
        logger.error(f" {e}")
        return None


def generate_body_comment(
    name: str,
    event_type: str,
    feature_states: typing.List[typing.Dict[str, typing.Any]],
) -> str:

    is_update = event_type == WebhookEventType.FLAG_UPDATED.value
    is_removed = event_type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
    delete_text = UNLINKED_FEATURE_TEXT % (name,)

    if is_removed:
        return delete_text

    last_updated_string = LAST_UPDATED_FEATURE_TEXT % (
        datetime.datetime.now().strftime("%dth %b %Y %I:%M%p")
    )
    updated_text = UPDATED_FEATURE_TEXT % (name)

    result = updated_text if is_update else LINK_FEATURE_TEXT % (name)

    # if feature_states is None:
    for v in feature_states:
        feature_value = v.get("feature_state_value")
        feature_value_type = v.get("feature_state_value_type")

        feature_value_string = f"\n{feature_value_type}\n```{feature_value if feature_value else 'No value.'}```\n\n"

        result += f"**{v['environment_name']}{' - ' + v['segment_name'] if v.get('segment_name') else ''}**\n"
        result += f"- [{'x' if v['feature_value'] else ' '}] {'Enabled' if v['feature_value'] else 'Disabled'}"
        result += feature_value_string

    result += last_updated_string
    return result


def check_not_none(value: any) -> bool:
    return value is not None


def generate_data(
    github_configuration: GithubConfiguration,
    feature_id: int,
    feature_name: str,
    type: str,
    feature_states: typing.Union[list[FeatureState], list[FeatureStateValue]] = None,
    url: str = None,
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
                feature_env_data["feature_value"] = feature_state.enabled
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
    )

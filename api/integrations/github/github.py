import datetime
import logging
import typing

import requests
from django.conf import settings

from features.models import FeatureState, FeatureStateValue
from integrations.github.client import generate_token
from integrations.github.constants import GITHUB_API_URL
from integrations.github.models import GithubConfiguration
from webhooks.webhooks import WebhookEventType

logger = logging.getLogger(__name__)


def post_comment_to_github(installation_id, owner, repo, issue, body):
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
        response = requests.post(url, json=payload, headers=headers)

        return response.json() if response.status_code == 200 else None
    except requests.RequestException as e:
        logger.info(f" {e}")
        return None


def generate_body_comment(name, event_type, feature_states):
    def is_integer(value):
        return isinstance(value, int)

    def is_string(value):
        return isinstance(value, str)

    def is_boolean(value):
        return isinstance(value, bool)

    def parse_language(value):
        return ""

    is_update = event_type == WebhookEventType.FLAG_UPDATED.value
    is_removed = event_type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
    delete_text = f"### The feature flag {name} was unlinked from the issue/PR"

    if is_removed:
        return delete_text

    last_updated_string = (
        f"Last Updated {datetime.datetime.now().strftime('%dth %b %Y %I:%M%p')}"
    )
    updated_text = (
        f"### The Flagsmith Feature {name} "
        f"was updated in the environment {feature_states[0]['environment_name']}"
    )

    result = updated_text if is_update else f"title ({name}):\n"

    for v in feature_states:
        feature_value = (
            v.get("integer_value", "")
            if is_integer(v.get("integer_value"))
            else (
                v.get("string_value", "")
                if is_string(v.get("string_value"))
                else v.get("boolean_value", "")
            )
        )

        has_feature_value = feature_value is not None and feature_value != ""
        language = parse_language(feature_value) if has_feature_value else ""

        feature_value_string = (
            f"\n{language}\n```{feature_value if feature_value else 'No value.'}```\n\n"
        )

        result += f"**{v['environment_name']}{' - ' + v['segment_name'] if v.get('segment_name') else ''}**\n"
        result += f"- [{'x' if v['feature_value'] else ' '}] {'Enabled' if v['feature_value'] else 'Disabled'}"
        result += feature_value_string

    result += last_updated_string
    return result


def check_not_none(value) -> bool:
    return value is not None


def generate_data(
    github_configuration: GithubConfiguration,
    feature_id: int,
    feature_name: str,
    type: str,
    feature_states: typing.Union[list[FeatureState], list[FeatureStateValue]] = None,
    url: str = None,
):

    feature_data = {
        "id": feature_id,
        "name": feature_name,
    }

    feature_data["installation_id"] = github_configuration.installation_id
    feature_data["organisation_id"] = github_configuration.organisation.id

    if type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
        feature_data["url"] = url
    else:
        feature_data["feature_states"] = []
        for feature_state in feature_states:
            feature_env_data = {}
            if check_not_none(feature_state.feature_state_value.string_value):
                feature_env_data["string_value"] = (
                    feature_state.feature_state_value.string_value
                )
            if check_not_none(feature_state.feature_state_value.boolean_value):
                feature_env_data["boolean_value"] = (
                    feature_state.feature_state_value.boolean_value
                )
            if check_not_none(feature_state.feature_state_value.integer_value):
                feature_env_data["integer_value"] = (
                    feature_state.feature_state_value.integer_value
                )
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
            feature_data["feature_states"].append(feature_env_data)

    return feature_data

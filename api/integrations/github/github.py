import datetime
import logging

import requests

from features.models import FeatureState
from integrations.github.client import generate_token
from integrations.github.constants import GITHUB_API_URL, GITHUB_APP_ID
from integrations.github.models import GithubConfiguration
from integrations.github.tasks import call_github_app_webhook_for_feature_state
from webhooks.webhooks import WebhookEventType

logger = logging.getLogger(__name__)


def post_comment_to_github(installation_id, owner, repo, issue, body):
    try:
        token = generate_token(
            installation_id,
            GITHUB_APP_ID,
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
            else v.get("string_value", "")
            if is_string(v.get("string_value"))
            else v.get("boolean_value", "")
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


def generate_data(
    github_configuration: GithubConfiguration,
    feature_id: str,
    feature_name: str,
    webhook_even_type: str,
    environment_name: str,
    feature_value: bool,
    url: str,
):
    feature_data = {
        "id": feature_id,
        "name": feature_name,
        "feature_states": [],
    }
    if webhook_even_type == WebhookEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value:
        feature_states = FeatureState.objects.filter(feature_id=feature_id)

        for feature_state in feature_states:
            feature_env_data = {}
            if feature_state.feature_state_value.string_value is not None:
                feature_env_data[
                    "string_value"
                ] = feature_state.feature_state_value.string_value
            if feature_state.feature_state_value.boolean_value is not None:
                feature_env_data[
                    "boolean_value"
                ] = feature_state.feature_state_value.boolean_value
            if feature_state.feature_state_value.integer_value is not None:
                feature_env_data[
                    "integer_value"
                ] = feature_state.feature_state_value.integer_value

            feature_env_data["environment_name"] = environment_name
            feature_env_data["feature_value"] = feature_value
            if (
                hasattr(feature_state, "feature_segment")
                and feature_state.feature_segment is not None
            ):
                feature_env_data[
                    "segment_name"
                ] = feature_state.feature_segment.segment.name
            feature_data["feature_states"].append(feature_env_data)

    elif webhook_even_type == WebhookEventType.FLAG_UPDATED.value:
        feature_state = {
            "environment_name": environment_name,
            "feature_value": feature_value,
        }

        # if instance.feature_state_value.string_value is not None:
        #     feature_state["string_value"] = instance.feature_state_value.string_value
        # if instance.feature_state_value.boolean_value is not None:
        #     feature_state["boolean_value"] = instance.feature_state_value.boolean_value
        # if instance.feature_state_value.integer_value is not None:
        #     feature_state["integer_value"] = instance.feature_state_value.integer_value
        # if (
        #     hasattr(feature_state, "feature_segment")
        #     and instance.feature_segment is not None
        # ):
        #     feature_state["segment_name"] = instance.feature_segment.segment.name

        # feature_data["feature_states"].append(feature_state)

    feature_data["installation_id"] = github_configuration.installation_id
    feature_data["organisation_id"] = github_configuration.organisation.id

    if url:
        feature_data["url"] = url

    call_github_app_webhook_for_feature_state.delay(
        args=(
            feature_data,
            webhook_even_type,
        ),
    )

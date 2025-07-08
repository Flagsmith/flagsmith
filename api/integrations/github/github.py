import logging
import typing
from dataclasses import asdict
from typing import Any

from django.db.models import Q
from django.utils.formats import get_format

from core.helpers import get_current_site_url
from features.models import Feature, FeatureState, FeatureStateValue
from integrations.github.constants import (
    DELETED_FEATURE_TEXT,
    DELETED_SEGMENT_OVERRIDE_TEXT,
    FEATURE_ENVIRONMENT_URL,
    FEATURE_TABLE_HEADER,
    FEATURE_TABLE_ROW,
    GITHUB_TAG_COLOR,
    LINK_FEATURE_TITLE,
    LINK_SEGMENT_TITLE,
    UNLINKED_FEATURE_TEXT,
    UPDATED_FEATURE_TEXT,
    GitHubEventType,
    GitHubTag,
    github_tag_description,
)
from integrations.github.dataclasses import GithubData
from integrations.github.models import GithubConfiguration, GitHubRepository
from integrations.github.tasks import call_github_app_webhook_for_feature_state
from projects.tags.models import Tag, TagType

logger = logging.getLogger(__name__)

tag_by_event_type = {
    "pull_request": {
        "closed": GitHubTag.PR_CLOSED.value,
        "converted_to_draft": GitHubTag.PR_DRAFT.value,
        "opened": GitHubTag.PR_OPEN.value,
        "reopened": GitHubTag.PR_OPEN.value,
        "dequeued": GitHubTag.PR_DEQUEUED.value,
        "ready_for_review": GitHubTag.PR_OPEN.value,
        "merged": GitHubTag.PR_MERGED.value,
    },
    "issues": {
        "closed": GitHubTag.ISSUE_CLOSED.value,
        "opened": GitHubTag.ISSUE_OPEN.value,
        "reopened": GitHubTag.ISSUE_OPEN.value,
    },
}


def tag_feature_per_github_event(
    event_type: str, action: str, metadata: dict[str, Any], repo_full_name: str
) -> None:
    # Get Feature with external resource of type GITHUB and url matching the resource URL
    feature = Feature.objects.filter(
        Q(external_resources__type="GITHUB_PR")
        | Q(external_resources__type="GITHUB_ISSUE"),
        external_resources__url=metadata.get("html_url"),
    ).first()

    # Check to see if any feature objects match and if not return
    # to allow the webhook processing complete.
    if not feature:
        return

    repository_owner, repository_name = repo_full_name.split(sep="/", maxsplit=1)
    tagging_enabled = GitHubRepository.objects.get(
        project=feature.project,
        repository_owner=repository_owner,
        repository_name=repository_name,
    ).tagging_enabled

    if tagging_enabled:
        if (
            event_type == "pull_request"
            and action == "closed"
            and metadata.get("merged")
        ):
            action = "merged"
        # Get or create the corresponding project Tag to tag the feature
        github_tag, _ = Tag.objects.get_or_create(
            color=GITHUB_TAG_COLOR,
            description=github_tag_description[tag_by_event_type[event_type][action]],
            label=tag_by_event_type[event_type][action],
            project=feature.project,
            is_system_tag=True,
            type=TagType.GITHUB.value,
        )
        tag_label_pattern = "Issue" if event_type == "issues" else "PR"
        # Remove all GITHUB tags from the feature which label starts with issue or pr depending on event_type
        feature.tags.remove(
            *feature.tags.filter(
                Q(type=TagType.GITHUB.value) & Q(label__startswith=tag_label_pattern)
            )
        )

        feature.tags.add(github_tag)
        feature.save()


def handle_installation_deleted(payload: dict[str, Any]) -> None:
    installation_id = payload.get("installation", {}).get("id")
    if installation_id is not None:
        try:
            GithubConfiguration.objects.get(installation_id=installation_id).delete()
        except GithubConfiguration.DoesNotExist:
            logger.error(
                f"GitHub Configuration with installation_id {installation_id} does not exist"
            )
    else:
        logger.error(f"The installation_id is not present in the payload: {payload}")


def handle_github_webhook_event(event_type: str, payload: dict[str, Any]) -> None:
    if event_type == "installation" and payload.get("action") == "deleted":
        return handle_installation_deleted(payload)

    action = str(payload.get("action"))
    if action in tag_by_event_type[event_type]:
        repo_full_name = payload["repository"]["full_name"]
        metadata = payload.get("issue", {}) or payload.get("pull_request", {})
        tag_feature_per_github_event(event_type, action, metadata, repo_full_name)


def generate_body_comment(
    name: str,
    event_type: str,
    feature_id: int,
    feature_states: list[dict[str, typing.Any]],
    project_id: int | None = None,
    segment_name: str | None = None,
) -> str:
    is_removed = event_type == GitHubEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
    is_segment_override_deleted = (
        event_type == GitHubEventType.SEGMENT_OVERRIDE_DELETED.value
    )

    if event_type == GitHubEventType.FLAG_DELETED.value:
        return DELETED_FEATURE_TEXT % (name)

    if is_removed:
        return UNLINKED_FEATURE_TEXT % (name)

    if is_segment_override_deleted and segment_name is not None:
        return DELETED_SEGMENT_OVERRIDE_TEXT % (segment_name, name)

    result = ""
    if event_type == GitHubEventType.FLAG_UPDATED.value:
        result = UPDATED_FEATURE_TEXT % (name)
    else:
        result = LINK_FEATURE_TITLE % (name)

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


def check_not_none(value: Any) -> bool:
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
    feature_states_list = []

    if feature_states:
        for feature_state in feature_states:
            feature_state_value = feature_state.get_feature_state_value()
            feature_env_data = {}

            if check_not_none(feature_state_value):
                feature_env_data["feature_state_value"] = feature_state_value

            if type is not GitHubEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
                feature_env_data["environment_name"] = feature_state.environment.name  # type: ignore[union-attr]
                feature_env_data["enabled"] = feature_state.enabled
                feature_env_data["last_updated"] = feature_state.updated_at.strftime(
                    get_format("DATETIME_INPUT_FORMATS")[0]
                )
                feature_env_data["environment_api_key"] = (
                    feature_state.environment.api_key  # type: ignore[union-attr]
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
            if type == GitHubEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
            else None
        ),
        feature_states=feature_states_list,
        project_id=feature.project_id,
        segment_name=segment_name,
    )


def call_github_task(
    organisation_id: str,
    type: str,
    feature: Feature,
    segment_name: str | None,
    url: str | None,
    feature_states: typing.Union[list[typing.Any], list[typing.Any]] | None,
) -> None:
    github_configuration = GithubConfiguration.objects.get(
        organisation_id=organisation_id
    )

    feature_data: GithubData = generate_data(
        github_configuration=github_configuration,
        feature=feature,
        type=type,
        url=url,
        segment_name=segment_name,
        feature_states=feature_states,
    )

    call_github_app_webhook_for_feature_state.delay(
        args=(asdict(feature_data),),
    )

import logging
import typing
from dataclasses import asdict
from typing import Any

from django.db.models import Q
from django.utils.formats import get_format

from features.models import Feature, FeatureState, FeatureStateValue
from integrations.gitlab.constants import (
    GITLAB_TAG_COLOR,
    UNLINKED_FEATURE_TEXT,
    GitLabEventType,
    GitLabTag,
    gitlab_tag_description,
)
from integrations.gitlab.dataclasses import GitLabData
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.tasks import call_gitlab_app_webhook_for_feature_state
from projects.tags.models import Tag, TagType

logger = logging.getLogger(__name__)

tag_by_event_type: dict[str, dict[str, str | None]] = {
    "merge_request": {
        "close": GitLabTag.MR_CLOSED.value,
        "merge": GitLabTag.MR_MERGED.value,
        "open": GitLabTag.MR_OPEN.value,
        "reopen": GitLabTag.MR_OPEN.value,
        "update": None,  # handled separately for draft detection
    },
    "issue": {
        "close": GitLabTag.ISSUE_CLOSED.value,
        "open": GitLabTag.ISSUE_OPEN.value,
        "reopen": GitLabTag.ISSUE_OPEN.value,
    },
}


def _get_tag_value_for_event(
    event_type: str, action: str, metadata: dict[str, Any]
) -> str | None:
    """Return the tag value string for a GitLab event, or None if no tag change is needed."""
    if event_type == "merge_request" and action == "update":
        if metadata.get("draft", False):
            return GitLabTag.MR_DRAFT.value
        # Generic update — no tag change needed
        return None
    if event_type in tag_by_event_type and action in tag_by_event_type[event_type]:
        return tag_by_event_type[event_type][action]
    return None


def tag_feature_per_gitlab_event(
    event_type: str,
    action: str,
    metadata: dict[str, Any],
    project_path: str,
) -> None:
    web_url = metadata.get("web_url", "")

    # GitLab webhooks send /-/issues/N but the stored URL might be /-/work_items/N
    # Try both URL variants to find the linked feature
    url_variants = [web_url]
    if "/-/issues/" in web_url:
        url_variants.append(web_url.replace("/-/issues/", "/-/work_items/"))
    elif "/-/work_items/" in web_url:
        url_variants.append(web_url.replace("/-/work_items/", "/-/issues/"))

    feature = None
    for url in url_variants:
        feature = Feature.objects.filter(
            Q(external_resources__type="GITLAB_MR")
            | Q(external_resources__type="GITLAB_ISSUE"),
            external_resources__url=url,
        ).first()
        if feature:
            break

    if not feature:
        return None

    try:
        gitlab_config = GitLabConfiguration.objects.get(
            project=feature.project,
            project_name=project_path,
        )
    except GitLabConfiguration.DoesNotExist:
        return None

    if gitlab_config.tagging_enabled:
        tag_value = _get_tag_value_for_event(event_type, action, metadata)

        if tag_value is None:
            return None

        gitlab_tag, _ = Tag.objects.get_or_create(
            color=GITLAB_TAG_COLOR,
            description=gitlab_tag_description[tag_value],
            label=tag_value,
            project=feature.project,
            is_system_tag=True,
            type=TagType.GITLAB.value,
        )
        tag_label_pattern = "Issue" if event_type == "issue" else "MR"
        feature.tags.remove(
            *feature.tags.filter(
                Q(type=TagType.GITLAB.value) & Q(label__startswith=tag_label_pattern)
            )
        )
        feature.tags.add(gitlab_tag)
        feature.save()

    return None


def handle_gitlab_webhook_event(event_type: str, payload: dict[str, Any]) -> None:
    if event_type == "merge_request":
        attrs = payload.get("object_attributes", {})
        action = attrs.get("action", "")
        project_path = payload.get("project", {}).get("path_with_namespace", "")
        metadata = {
            "web_url": attrs.get("url", ""),
            "draft": attrs.get("work_in_progress", False),
            "merged": attrs.get("state") == "merged",
        }
        tag_feature_per_gitlab_event(event_type, action, metadata, project_path)
    elif event_type == "issue":
        attrs = payload.get("object_attributes", {})
        action = attrs.get("action", "")
        project_path = payload.get("project", {}).get("path_with_namespace", "")
        metadata = {"web_url": attrs.get("url", "")}
        tag_feature_per_gitlab_event(event_type, action, metadata, project_path)


def generate_body_comment(
    name: str,
    event_type: str,
    feature_id: int,
    feature_states: list[dict[str, typing.Any]],
    project_id: int | None = None,
    segment_name: str | None = None,
) -> str:
    from integrations.vcs.comments import (
        generate_body_comment as _generate_body_comment,
    )

    return _generate_body_comment(
        name=name,
        event_type=event_type,
        feature_id=feature_id,
        feature_states=feature_states,
        unlinked_feature_text=UNLINKED_FEATURE_TEXT,
        project_id=project_id,
        segment_name=segment_name,
    )


def generate_data(
    gitlab_configuration: GitLabConfiguration,
    feature: Feature,
    type: str,
    feature_states: (
        typing.Union[list[FeatureState], list[FeatureStateValue]] | None
    ) = None,
    url: str | None = None,
    segment_name: str | None = None,
) -> GitLabData:
    feature_states_list: list[dict[str, Any]] = []

    if feature_states:
        for feature_state in feature_states:
            feature_state_value = feature_state.get_feature_state_value()
            feature_env_data: dict[str, Any] = {}

            if feature_state_value is not None:
                feature_env_data["feature_state_value"] = feature_state_value

            if type is not GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value:
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

    return GitLabData(
        feature_id=feature.id,
        feature_name=feature.name,
        gitlab_instance_url=gitlab_configuration.gitlab_instance_url,
        access_token=gitlab_configuration.access_token,
        type=type,
        url=(
            url
            if type == GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
            else None
        ),
        feature_states=feature_states_list,
        project_id=feature.project_id,
        segment_name=segment_name,
    )


def call_gitlab_task(
    project_id: int,
    type: str,
    feature: Feature,
    segment_name: str | None,
    url: str | None,
    feature_states: typing.Union[list[typing.Any], list[typing.Any]] | None,
) -> None:
    gitlab_configuration = GitLabConfiguration.objects.get(project_id=project_id)

    feature_data: GitLabData = generate_data(
        gitlab_configuration=gitlab_configuration,
        feature=feature,
        type=type,
        url=url,
        segment_name=segment_name,
        feature_states=feature_states,
    )

    call_gitlab_app_webhook_for_feature_state.delay(
        args=(asdict(feature_data),),
    )

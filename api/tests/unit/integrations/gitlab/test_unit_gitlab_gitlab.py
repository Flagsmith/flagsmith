from dataclasses import asdict
from typing import Any

import pytest
from pytest_mock import MockerFixture

from features.feature_external_resources.models import (
    FeatureExternalResource,
)
from features.models import Feature
from integrations.gitlab.constants import (
    DELETED_FEATURE_TEXT,
    DELETED_SEGMENT_OVERRIDE_TEXT,
    LINK_FEATURE_TITLE,
    UNLINKED_FEATURE_TEXT,
    UPDATED_FEATURE_TEXT,
    GitLabEventType,
    GitLabTag,
)
from integrations.gitlab.dataclasses import (
    CallGitLabData,
    GitLabData,
    PaginatedQueryParams,
)
from integrations.gitlab.gitlab import (
    _get_tag_value_for_event,
    call_gitlab_task,
    generate_body_comment,
    generate_data,
    handle_gitlab_webhook_event,
    tag_feature_per_gitlab_event,
)
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.tasks import (
    _post_to_resource,
    _resolve_resource_urls_for_event,
    call_gitlab_app_webhook_for_feature_state,
    send_post_request,
)
from projects.tags.models import TagType

# ---------------------------------------------------------------
# _get_tag_value_for_event tests
# ---------------------------------------------------------------


def test_get_tag_value_for_event__mr_close__returns_mr_closed() -> None:
    # Given
    event_type = "merge_request"
    action = "close"
    metadata: dict[str, object] = {}

    # When
    result = _get_tag_value_for_event(event_type, action, metadata)

    # Then
    assert result == GitLabTag.MR_CLOSED.value


def test_get_tag_value_for_event__mr_merge__returns_mr_merged() -> None:
    # Given
    event_type = "merge_request"
    action = "merge"
    metadata: dict[str, object] = {}

    # When
    result = _get_tag_value_for_event(event_type, action, metadata)

    # Then
    assert result == GitLabTag.MR_MERGED.value


def test_get_tag_value_for_event__mr_open__returns_mr_open() -> None:
    # Given
    event_type = "merge_request"
    action = "open"
    metadata: dict[str, object] = {}

    # When
    result = _get_tag_value_for_event(event_type, action, metadata)

    # Then
    assert result == GitLabTag.MR_OPEN.value


def test_get_tag_value_for_event__mr_update_with_draft__returns_mr_draft() -> None:
    # Given
    event_type = "merge_request"
    action = "update"
    metadata = {"draft": True}

    # When
    result = _get_tag_value_for_event(event_type, action, metadata)

    # Then
    assert result == GitLabTag.MR_DRAFT.value


def test_get_tag_value_for_event__mr_update_without_draft__returns_none() -> None:
    # Given
    event_type = "merge_request"
    action = "update"
    metadata = {"draft": False}

    # When
    result = _get_tag_value_for_event(event_type, action, metadata)

    # Then
    assert result is None


def test_get_tag_value_for_event__issue_close__returns_issue_closed() -> None:
    # Given
    event_type = "issue"
    action = "close"
    metadata: dict[str, object] = {}

    # When
    result = _get_tag_value_for_event(event_type, action, metadata)

    # Then
    assert result == GitLabTag.ISSUE_CLOSED.value


def test_get_tag_value_for_event__issue_open__returns_issue_open() -> None:
    # Given
    event_type = "issue"
    action = "open"
    metadata: dict[str, object] = {}

    # When
    result = _get_tag_value_for_event(event_type, action, metadata)

    # Then
    assert result == GitLabTag.ISSUE_OPEN.value


def test_get_tag_value_for_event__issue_reopen__returns_issue_open() -> None:
    # Given
    event_type = "issue"
    action = "reopen"
    metadata: dict[str, object] = {}

    # When
    result = _get_tag_value_for_event(event_type, action, metadata)

    # Then
    assert result == GitLabTag.ISSUE_OPEN.value


def test_get_tag_value_for_event__unknown_action__returns_none() -> None:
    # Given
    event_type = "issue"
    action = "unknown_action"
    metadata: dict[str, object] = {}

    # When
    result = _get_tag_value_for_event(event_type, action, metadata)

    # Then
    assert result is None


def test_get_tag_value_for_event__unknown_event_type__returns_none() -> None:
    # Given
    event_type = "push"
    action = "open"
    metadata: dict[str, object] = {}

    # When
    result = _get_tag_value_for_event(event_type, action, metadata)

    # Then
    assert result is None


# ---------------------------------------------------------------
# tag_feature_per_gitlab_event tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_tag_feature_per_gitlab_event__empty_feature__returns_none() -> None:
    # Given
    # No feature is linked to the given URL in the database

    # When / Then - should not raise
    tag_feature_per_gitlab_event(
        event_type="merge_request",
        action="merge",
        metadata={"web_url": "https://gitlab.com/group/project/-/merge_requests/1"},
        project_path="group/project",
    )


@pytest.mark.django_db
def test_tag_feature_per_gitlab_event__matching_feature_tagging_enabled__adds_tag(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    web_url = "https://gitlab.example.com/testgroup/testrepo/-/merge_requests/1"
    FeatureExternalResource.objects.create(
        url=web_url,
        type="GITLAB_MR",
        feature=feature,
        metadata='{"state": "opened"}',
    )

    # When
    tag_feature_per_gitlab_event(
        event_type="merge_request",
        action="merge",
        metadata={"web_url": web_url},
        project_path="testgroup/testrepo",
    )

    # Then
    feature.refresh_from_db()
    tag_labels = list(feature.tags.values_list("label", flat=True))
    assert GitLabTag.MR_MERGED.value in tag_labels


@pytest.mark.django_db
def test_tag_feature_per_gitlab_event__tagging_disabled__does_not_tag(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    gitlab_configuration.tagging_enabled = False
    gitlab_configuration.save()

    web_url = "https://gitlab.example.com/testgroup/testrepo/-/merge_requests/1"
    FeatureExternalResource.objects.create(
        url=web_url,
        type="GITLAB_MR",
        feature=feature,
        metadata='{"state": "opened"}',
    )

    # When
    tag_feature_per_gitlab_event(
        event_type="merge_request",
        action="merge",
        metadata={"web_url": web_url},
        project_path="testgroup/testrepo",
    )

    # Then
    feature.refresh_from_db()
    gitlab_tags = feature.tags.filter(type=TagType.GITLAB.value)
    assert not gitlab_tags.filter(label=GitLabTag.MR_MERGED.value).exists()


@pytest.mark.django_db
def test_tag_feature_per_gitlab_event__work_items_url_variant__finds_feature(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given - feature linked with work_items URL, but webhook sends issues URL
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    work_items_url = "https://gitlab.example.com/testgroup/testrepo/-/work_items/5"
    FeatureExternalResource.objects.create(
        url=work_items_url,
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )

    issues_url = "https://gitlab.example.com/testgroup/testrepo/-/issues/5"

    # When
    tag_feature_per_gitlab_event(
        event_type="issue",
        action="close",
        metadata={"web_url": issues_url},
        project_path="testgroup/testrepo",
    )

    # Then
    feature.refresh_from_db()
    tag_labels = list(feature.tags.values_list("label", flat=True))
    assert GitLabTag.ISSUE_CLOSED.value in tag_labels


@pytest.mark.django_db
def test_tag_feature_per_gitlab_event__no_gitlab_config__returns_none(
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given - feature has external resource but no GitLab config
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    web_url = "https://gitlab.example.com/testgroup/testrepo/-/merge_requests/1"
    FeatureExternalResource.objects.create(
        url=web_url,
        type="GITLAB_MR",
        feature=feature,
        metadata='{"state": "opened"}',
    )

    # When
    tag_feature_per_gitlab_event(
        event_type="merge_request",
        action="merge",
        metadata={"web_url": web_url},
        project_path="testgroup/testrepo",
    )

    # Then
    assert feature.tags.count() == 0


@pytest.mark.django_db
def test_tag_feature_per_gitlab_event__null_tag_value__returns_none(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given - MR update without draft = no tag change
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    web_url = "https://gitlab.example.com/testgroup/testrepo/-/merge_requests/1"
    FeatureExternalResource.objects.create(
        url=web_url,
        type="GITLAB_MR",
        feature=feature,
        metadata='{"state": "opened"}',
    )

    # When
    tag_feature_per_gitlab_event(
        event_type="merge_request",
        action="update",
        metadata={"web_url": web_url, "draft": False},
        project_path="testgroup/testrepo",
    )

    # Then
    assert feature.tags.count() == 0


# ---------------------------------------------------------------
# handle_gitlab_webhook_event tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_handle_gitlab_webhook_event__merge_request__calls_tag_feature(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_tag = mocker.patch("integrations.gitlab.gitlab.tag_feature_per_gitlab_event")
    payload = {
        "object_attributes": {
            "action": "merge",
            "url": "https://gitlab.example.com/group/project/-/merge_requests/1",
            "state": "merged",
            "work_in_progress": False,
        },
        "project": {
            "path_with_namespace": "group/project",
        },
    }

    # When
    handle_gitlab_webhook_event(event_type="merge_request", payload=payload)

    # Then
    mock_tag.assert_called_once_with(
        "merge_request",
        "merge",
        {
            "web_url": "https://gitlab.example.com/group/project/-/merge_requests/1",
            "draft": False,
            "merged": True,
        },
        "group/project",
    )


@pytest.mark.django_db
def test_handle_gitlab_webhook_event__issue__calls_tag_feature(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_tag = mocker.patch("integrations.gitlab.gitlab.tag_feature_per_gitlab_event")
    payload = {
        "object_attributes": {
            "action": "close",
            "url": "https://gitlab.example.com/group/project/-/issues/5",
        },
        "project": {
            "path_with_namespace": "group/project",
        },
    }

    # When
    handle_gitlab_webhook_event(event_type="issue", payload=payload)

    # Then
    mock_tag.assert_called_once_with(
        "issue",
        "close",
        {"web_url": "https://gitlab.example.com/group/project/-/issues/5"},
        "group/project",
    )


def test_handle_gitlab_webhook_event__unknown_event__does_nothing(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_tag = mocker.patch("integrations.gitlab.gitlab.tag_feature_per_gitlab_event")

    # When
    handle_gitlab_webhook_event(event_type="push", payload={})

    # Then
    mock_tag.assert_not_called()


# ---------------------------------------------------------------
# generate_body_comment tests
# ---------------------------------------------------------------


def test_generate_body_comment__flag_deleted__returns_deleted_text() -> None:
    # Given
    event_type = GitLabEventType.FLAG_DELETED.value

    # When
    result = generate_body_comment(
        name="my_flag",
        event_type=event_type,
        feature_id=1,
        feature_states=[],
    )

    # Then
    assert result == DELETED_FEATURE_TEXT % "my_flag"


def test_generate_body_comment__resource_removed__returns_unlinked_text() -> None:
    # Given
    event_type = GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value

    # When
    result = generate_body_comment(
        name="my_flag",
        event_type=event_type,
        feature_id=1,
        feature_states=[],
    )

    # Then
    assert result == UNLINKED_FEATURE_TEXT % "my_flag"


def test_generate_body_comment__segment_override_deleted__returns_segment_deleted_text() -> (
    None
):
    # Given
    event_type = GitLabEventType.SEGMENT_OVERRIDE_DELETED.value

    # When
    result = generate_body_comment(
        name="my_flag",
        event_type=event_type,
        feature_id=1,
        feature_states=[],
        segment_name="my_segment",
    )

    # Then
    assert result == DELETED_SEGMENT_OVERRIDE_TEXT % ("my_segment", "my_flag")


def test_generate_body_comment__flag_updated__returns_updated_text_with_table(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.gitlab.gitlab.get_current_site_url",
        return_value="https://example.com",
    )
    event_type = GitLabEventType.FLAG_UPDATED.value
    feature_states = [
        {
            "environment_name": "Production",
            "enabled": True,
            "feature_state_value": "on",
            "last_updated": "2024-01-01 00:00:00",
            "environment_api_key": "api-key-123",
        }
    ]

    # When
    result = generate_body_comment(
        name="my_flag",
        event_type=event_type,
        feature_id=42,
        feature_states=feature_states,
        project_id=10,
    )

    # Then
    assert UPDATED_FEATURE_TEXT % "my_flag" in result
    assert "Production" in result
    assert "Enabled" in result


def test_generate_body_comment__resource_added_with_feature_states__returns_linked_text(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.gitlab.gitlab.get_current_site_url",
        return_value="https://example.com",
    )
    event_type = GitLabEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value
    feature_states = [
        {
            "environment_name": "Dev",
            "enabled": False,
            "feature_state_value": None,
            "last_updated": "2024-01-01 00:00:00",
            "environment_api_key": "api-key-dev",
        }
    ]

    # When
    result = generate_body_comment(
        name="my_flag",
        event_type=event_type,
        feature_id=42,
        feature_states=feature_states,
        project_id=10,
    )

    # Then
    assert LINK_FEATURE_TITLE % "my_flag" in result
    assert "Dev" in result
    assert "Disabled" in result


def test_generate_body_comment__with_segment_feature_states__includes_segment_header(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.gitlab.gitlab.get_current_site_url",
        return_value="https://example.com",
    )
    event_type = GitLabEventType.FLAG_UPDATED.value
    feature_states = [
        {
            "environment_name": "Production",
            "enabled": True,
            "feature_state_value": "v1",
            "last_updated": "2024-01-01 00:00:00",
            "environment_api_key": "api-key-prod",
            "segment_name": "beta_users",
        }
    ]

    # When
    result = generate_body_comment(
        name="my_flag",
        event_type=event_type,
        feature_id=42,
        feature_states=feature_states,
        project_id=10,
    )

    # Then
    assert "beta_users" in result
    assert "segment-overrides" in result


# ---------------------------------------------------------------
# generate_data tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_generate_data__with_feature_states__returns_gitlab_data(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    environment: Any,
    mocker: MockerFixture,
) -> None:
    # Given
    from features.models import FeatureState

    feature_state = FeatureState.objects.filter(
        feature=feature, identity__isnull=True
    ).first()
    assert feature_state is not None

    # When
    result = generate_data(
        gitlab_configuration=gitlab_configuration,
        feature=feature,
        type=GitLabEventType.FLAG_UPDATED.value,
        feature_states=[feature_state],
    )

    # Then
    assert result.feature_id == feature.id
    assert result.feature_name == feature.name
    assert result.type == GitLabEventType.FLAG_UPDATED.value
    assert len(result.feature_states) == 1
    assert "environment_name" in result.feature_states[0]
    assert result.url is None


@pytest.mark.django_db
def test_generate_data__feature_state_with_value__includes_feature_state_value(
    gitlab_configuration: GitLabConfiguration,
    environment: Any,
) -> None:
    # Given
    from features.models import Feature, FeatureState

    feature_with_val = Feature.objects.create(
        name="flag_with_value",
        initial_value="some_value",
        project=gitlab_configuration.project,
    )
    feature_state = FeatureState.objects.filter(
        feature=feature_with_val,
        identity__isnull=True,
        environment=environment,
    ).first()
    assert feature_state is not None

    # When
    result = generate_data(
        gitlab_configuration=gitlab_configuration,
        feature=feature_with_val,
        type=GitLabEventType.FLAG_UPDATED.value,
        feature_states=[feature_state],
    )

    # Then — line 224: feature_state_value is set
    assert len(result.feature_states) == 1
    assert result.feature_states[0]["feature_state_value"] == "some_value"


@pytest.mark.django_db
def test_generate_data__without_feature_states__returns_empty_list(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given / When
    result = generate_data(
        gitlab_configuration=gitlab_configuration,
        feature=feature,
        type=GitLabEventType.FLAG_DELETED.value,
    )

    # Then
    assert result.feature_states == []
    assert result.url is None


@pytest.mark.django_db
def test_generate_data__resource_removed__sets_url(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    removed_url = "https://gitlab.example.com/group/project/-/issues/5"

    # When
    result = generate_data(
        gitlab_configuration=gitlab_configuration,
        feature=feature,
        type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
        url=removed_url,
    )

    # Then
    assert result.url == removed_url


@pytest.mark.django_db
def test_generate_data__resource_removed_with_feature_states__skips_env_data(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    environment: Any,
) -> None:
    # Given
    from features.models import FeatureState

    feature_state = FeatureState.objects.filter(
        feature=feature, identity__isnull=True
    ).first()
    assert feature_state is not None

    # When
    result = generate_data(
        gitlab_configuration=gitlab_configuration,
        feature=feature,
        type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
        feature_states=[feature_state],
        url="https://gitlab.example.com/group/project/-/issues/1",
    )

    # Then — line 221 False branch: env data is NOT included for REMOVED events
    assert len(result.feature_states) == 1
    assert "environment_name" not in result.feature_states[0]
    assert "enabled" not in result.feature_states[0]


@pytest.mark.django_db
def test_generate_data__with_segment_feature_state__includes_segment_name(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    environment: Any,
    mocker: MockerFixture,
) -> None:
    # Given
    from features.models import FeatureState

    feature_state = FeatureState.objects.filter(
        feature=feature, identity__isnull=True
    ).first()
    assert feature_state is not None

    # When
    result = generate_data(
        gitlab_configuration=gitlab_configuration,
        feature=feature,
        type=GitLabEventType.FLAG_UPDATED.value,
        feature_states=[feature_state],
        segment_name="beta_segment",
    )

    # Then
    assert result.segment_name == "beta_segment"


# ---------------------------------------------------------------
# call_gitlab_task tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_call_gitlab_task__happy_path__calls_webhook_task(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_task = mocker.patch(
        "integrations.gitlab.gitlab.call_gitlab_app_webhook_for_feature_state"
    )

    # When
    call_gitlab_task(
        project_id=feature.project_id,
        type=GitLabEventType.FLAG_DELETED.value,
        feature=feature,
        segment_name=None,
        url=None,
        feature_states=None,
    )

    # Then
    mock_task.delay.assert_called_once()
    call_args = mock_task.delay.call_args
    assert call_args.kwargs["args"] is not None


# ---------------------------------------------------------------
# PaginatedQueryParams validation tests
# ---------------------------------------------------------------


def test_paginated_query_params__page_less_than_1__raises_value_error() -> None:
    # Given / When
    # Then
    with pytest.raises(ValueError, match="Page must be greater or equal than 1"):
        PaginatedQueryParams(page=0, page_size=10)


def test_paginated_query_params__page_size_too_large__raises_value_error() -> None:
    # Given / When
    # Then
    with pytest.raises(
        ValueError, match="Page size must be an integer between 1 and 100"
    ):
        PaginatedQueryParams(page=1, page_size=101)


def test_paginated_query_params__page_size_less_than_1__raises_value_error() -> None:
    # Given / When
    # Then
    with pytest.raises(
        ValueError, match="Page size must be an integer between 1 and 100"
    ):
        PaginatedQueryParams(page=1, page_size=0)


# ---------------------------------------------------------------
# _resolve_resource_urls_for_event tests
# ---------------------------------------------------------------


def test_resolve_resource_urls_for_event__flag_updated__returns_all_resource_urls() -> (
    None
):
    # Given
    gitlab_data = GitLabData(
        gitlab_instance_url="https://gitlab.example.com",
        access_token="token",
        feature_id=1,
        feature_name="test_flag",
        type=GitLabEventType.FLAG_UPDATED.value,
    )
    data = CallGitLabData(
        event_type=GitLabEventType.FLAG_UPDATED.value,
        gitlab_data=gitlab_data,
        feature_external_resources=[
            {
                "type": "GITLAB_ISSUE",
                "url": "https://gitlab.example.com/group/project/-/issues/1",
            },
            {
                "type": "GITLAB_MR",
                "url": "https://gitlab.example.com/group/project/-/merge_requests/2",
            },
        ],
    )

    # When
    result = _resolve_resource_urls_for_event(data)

    # Then
    assert len(result) == 2
    assert "issues/1" in result[0]
    assert "merge_requests/2" in result[1]


def test_resolve_resource_urls_for_event__flag_deleted__returns_all_resource_urls() -> (
    None
):
    # Given
    gitlab_data = GitLabData(
        gitlab_instance_url="https://gitlab.example.com",
        access_token="token",
        feature_id=1,
        feature_name="test_flag",
        type=GitLabEventType.FLAG_DELETED.value,
    )
    data = CallGitLabData(
        event_type=GitLabEventType.FLAG_DELETED.value,
        gitlab_data=gitlab_data,
        feature_external_resources=[
            {
                "type": "GITLAB_ISSUE",
                "url": "https://gitlab.example.com/group/project/-/issues/1",
            },
        ],
    )

    # When
    result = _resolve_resource_urls_for_event(data)

    # Then
    assert len(result) == 1


def test_resolve_resource_urls_for_event__resource_removed_with_url__returns_url() -> (
    None
):
    # Given
    gitlab_data = GitLabData(
        gitlab_instance_url="https://gitlab.example.com",
        access_token="token",
        feature_id=1,
        feature_name="test_flag",
        type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
        url="https://gitlab.example.com/group/project/-/issues/5",
    )
    data = CallGitLabData(
        event_type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
        gitlab_data=gitlab_data,
        feature_external_resources=[],
    )

    # When
    result = _resolve_resource_urls_for_event(data)

    # Then
    assert result == ["https://gitlab.example.com/group/project/-/issues/5"]


def test_resolve_resource_urls_for_event__resource_removed_no_url__returns_empty() -> (
    None
):
    # Given
    gitlab_data = GitLabData(
        gitlab_instance_url="https://gitlab.example.com",
        access_token="token",
        feature_id=1,
        feature_name="test_flag",
        type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
        url=None,
    )
    data = CallGitLabData(
        event_type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
        gitlab_data=gitlab_data,
        feature_external_resources=[],
    )

    # When
    result = _resolve_resource_urls_for_event(data)

    # Then
    assert result == []


def test_resolve_resource_urls_for_event__default_case__returns_last_resource() -> None:
    # Given
    gitlab_data = GitLabData(
        gitlab_instance_url="https://gitlab.example.com",
        access_token="token",
        feature_id=1,
        feature_name="test_flag",
        type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
    )
    data = CallGitLabData(
        event_type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
        gitlab_data=gitlab_data,
        feature_external_resources=[
            {
                "type": "GITLAB_ISSUE",
                "url": "https://gitlab.example.com/group/project/-/issues/1",
            },
            {
                "type": "GITLAB_MR",
                "url": "https://gitlab.example.com/group/project/-/merge_requests/2",
            },
        ],
    )

    # When
    result = _resolve_resource_urls_for_event(data)

    # Then
    assert len(result) == 1
    assert "merge_requests/2" in result[0]


def test_resolve_resource_urls_for_event__default_empty_resources__returns_empty() -> (
    None
):
    # Given
    gitlab_data = GitLabData(
        gitlab_instance_url="https://gitlab.example.com",
        access_token="token",
        feature_id=1,
        feature_name="test_flag",
        type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
    )
    data = CallGitLabData(
        event_type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
        gitlab_data=gitlab_data,
        feature_external_resources=[],
    )

    # When
    result = _resolve_resource_urls_for_event(data)

    # Then
    assert result == []


# ---------------------------------------------------------------
# _post_to_resource tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_post_to_resource__mr_url__posts_to_merge_requests(
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_post_comment = mocker.patch("integrations.gitlab.tasks.post_comment_to_gitlab")
    resource_url = "https://gitlab.example.com/testgroup/testrepo/-/merge_requests/3"

    # When
    _post_to_resource(
        resource_url=resource_url,
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        body="Test comment",
    )

    # Then
    mock_post_comment.assert_called_once_with(
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        gitlab_project_id=gitlab_configuration.gitlab_project_id,
        resource_type="merge_requests",
        resource_iid=3,
        body="Test comment",
    )


@pytest.mark.django_db
def test_post_to_resource__issue_url__posts_to_issues(
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_post_comment = mocker.patch("integrations.gitlab.tasks.post_comment_to_gitlab")
    resource_url = "https://gitlab.example.com/testgroup/testrepo/-/issues/7"

    # When
    _post_to_resource(
        resource_url=resource_url,
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        body="Test comment",
    )

    # Then
    mock_post_comment.assert_called_once_with(
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        gitlab_project_id=gitlab_configuration.gitlab_project_id,
        resource_type="issues",
        resource_iid=7,
        body="Test comment",
    )


@pytest.mark.django_db
def test_post_to_resource__work_items_url__posts_to_issues(
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_post_comment = mocker.patch("integrations.gitlab.tasks.post_comment_to_gitlab")
    resource_url = "https://gitlab.example.com/testgroup/testrepo/-/work_items/7"

    # When
    _post_to_resource(
        resource_url=resource_url,
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        body="Test comment",
    )

    # Then
    mock_post_comment.assert_called_once_with(
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        gitlab_project_id=gitlab_configuration.gitlab_project_id,
        resource_type="issues",
        resource_iid=7,
        body="Test comment",
    )


@pytest.mark.django_db
def test_post_to_resource__unknown_url_format__does_not_post(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_post_comment = mocker.patch("integrations.gitlab.tasks.post_comment_to_gitlab")
    resource_url = "https://gitlab.example.com/testgroup/testrepo/-/pipelines/1"

    # When
    _post_to_resource(
        resource_url=resource_url,
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        body="Test comment",
    )

    # Then
    mock_post_comment.assert_not_called()


@pytest.mark.django_db
def test_post_to_resource__missing_config__does_not_post(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_post_comment = mocker.patch("integrations.gitlab.tasks.post_comment_to_gitlab")
    resource_url = "https://gitlab.example.com/nonexistent/project/-/issues/1"

    # When
    _post_to_resource(
        resource_url=resource_url,
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        body="Test comment",
    )

    # Then
    mock_post_comment.assert_not_called()


def test_post_to_resource__no_iid_in_url__returns_early(
    mocker: MockerFixture,
) -> None:
    # Given — URL has /-/issues/ but no digits after it
    mock_post_comment = mocker.patch("integrations.gitlab.tasks.post_comment_to_gitlab")
    resource_url = "https://gitlab.example.com/group/project/-/issues/notanumber"

    # When
    _post_to_resource(
        resource_url=resource_url,
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        body="Test",
    )

    # Then — line 61: early return because iid_match is None
    mock_post_comment.assert_not_called()


def test_post_to_resource__no_project_path_match__returns_early(
    mocker: MockerFixture,
) -> None:
    # Given — URL has hyphens in the group name which breaks the [^/-] regex
    mock_post_comment = mocker.patch("integrations.gitlab.tasks.post_comment_to_gitlab")
    resource_url = "https://gitlab.example.com/my-group/my-project/-/issues/1"

    # When
    _post_to_resource(
        resource_url=resource_url,
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        body="Test",
    )

    # Then — line 68: early return because project_path_match is None
    mock_post_comment.assert_not_called()


# ---------------------------------------------------------------
# send_post_request tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_send_post_request__with_resources__calls_post_to_resource(
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_post_to_resource = mocker.patch("integrations.gitlab.tasks._post_to_resource")
    gitlab_data = GitLabData(
        gitlab_instance_url="https://gitlab.example.com",
        access_token="test-token",
        feature_id=1,
        feature_name="test_flag",
        type=GitLabEventType.FLAG_UPDATED.value,
        feature_states=[],
        project_id=1,
    )
    data = CallGitLabData(
        event_type=GitLabEventType.FLAG_UPDATED.value,
        gitlab_data=gitlab_data,
        feature_external_resources=[
            {
                "type": "GITLAB_ISSUE",
                "url": "https://gitlab.example.com/testgroup/testrepo/-/issues/1",
            },
        ],
    )

    # When
    send_post_request(data)

    # Then
    mock_post_to_resource.assert_called_once()


# ---------------------------------------------------------------
# call_gitlab_app_webhook_for_feature_state tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_call_gitlab_app_webhook_for_feature_state__flag_deleted__posts_to_resources(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/1",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )
    mock_send = mocker.patch("integrations.gitlab.tasks.send_post_request")

    event_data = asdict(
        GitLabData(
            gitlab_instance_url="https://gitlab.example.com",
            access_token="test-token",
            feature_id=feature.id,
            feature_name=feature.name,
            type=GitLabEventType.FLAG_DELETED.value,
            project_id=feature.project_id,
        )
    )

    # When
    call_gitlab_app_webhook_for_feature_state(event_data=event_data)

    # Then
    mock_send.assert_called_once()
    call_args = mock_send.call_args[0][0]
    assert call_args.event_type == GitLabEventType.FLAG_DELETED.value


@pytest.mark.django_db
def test_call_gitlab_app_webhook_for_feature_state__resource_removed__posts_with_url(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_send = mocker.patch("integrations.gitlab.tasks.send_post_request")
    removed_url = "https://gitlab.example.com/testgroup/testrepo/-/issues/1"

    event_data = asdict(
        GitLabData(
            gitlab_instance_url="https://gitlab.example.com",
            access_token="test-token",
            feature_id=feature.id,
            feature_name=feature.name,
            type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
            url=removed_url,
            project_id=feature.project_id,
        )
    )

    # When
    call_gitlab_app_webhook_for_feature_state(event_data=event_data)

    # Then
    mock_send.assert_called_once()
    call_args = mock_send.call_args[0][0]
    assert (
        call_args.event_type == GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value
    )
    assert call_args.feature_external_resources == []


@pytest.mark.django_db
def test_call_gitlab_app_webhook_for_feature_state__normal_update__posts_to_resources(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/1",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )
    mock_send = mocker.patch("integrations.gitlab.tasks.send_post_request")

    event_data = asdict(
        GitLabData(
            gitlab_instance_url="https://gitlab.example.com",
            access_token="test-token",
            feature_id=feature.id,
            feature_name=feature.name,
            type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
            project_id=feature.project_id,
        )
    )

    # When
    call_gitlab_app_webhook_for_feature_state(event_data=event_data)

    # Then
    mock_send.assert_called_once()
    call_args = mock_send.call_args[0][0]
    assert call_args.event_type == GitLabEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value
    assert len(call_args.feature_external_resources) == 1


@pytest.mark.django_db
def test_call_gitlab_app_webhook_for_feature_state__no_resources__does_not_send(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given - feature has no GitLab external resources
    mock_send = mocker.patch("integrations.gitlab.tasks.send_post_request")

    event_data = asdict(
        GitLabData(
            gitlab_instance_url="https://gitlab.example.com",
            access_token="test-token",
            feature_id=feature.id,
            feature_name=feature.name,
            type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_ADDED.value,
            project_id=feature.project_id,
        )
    )

    # When
    call_gitlab_app_webhook_for_feature_state(event_data=event_data)

    # Then
    mock_send.assert_not_called()


@pytest.mark.django_db
def test_call_gitlab_app_webhook_for_feature_state__segment_override_deleted__posts_to_resources(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/1",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )
    mock_send = mocker.patch("integrations.gitlab.tasks.send_post_request")

    event_data = asdict(
        GitLabData(
            gitlab_instance_url="https://gitlab.example.com",
            access_token="test-token",
            feature_id=feature.id,
            feature_name=feature.name,
            type=GitLabEventType.SEGMENT_OVERRIDE_DELETED.value,
            segment_name="my_segment",
            project_id=feature.project_id,
        )
    )

    # When
    call_gitlab_app_webhook_for_feature_state(event_data=event_data)

    # Then
    mock_send.assert_called_once()
    call_args = mock_send.call_args[0][0]
    assert call_args.event_type == GitLabEventType.SEGMENT_OVERRIDE_DELETED.value


# ---------------------------------------------------------------
# FeatureExternalResource model - GitLab hooks tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_handle_gitlab_after_save__with_config_and_tagging__adds_tag_and_calls_task(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_call_gitlab_task = mocker.patch(
        "integrations.gitlab.gitlab.call_gitlab_app_webhook_for_feature_state",
    )

    # When
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/10",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )

    # Then
    mock_call_gitlab_task.delay.assert_called_once()
    # Check tag was added
    feature.refresh_from_db()
    gitlab_tags = feature.tags.filter(type=TagType.GITLAB.value)
    assert gitlab_tags.exists()


@pytest.mark.django_db
def test_handle_gitlab_after_save__without_config__returns_early(
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given - no gitlab config
    mock_call_gitlab_task = mocker.patch(
        "integrations.gitlab.gitlab.call_gitlab_app_webhook_for_feature_state",
    )

    # When
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/10",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )

    # Then
    mock_call_gitlab_task.delay.assert_not_called()


@pytest.mark.django_db
def test_execute_before_save_actions__gitlab_delete__calls_task(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_call_task = mocker.patch(
        "integrations.gitlab.gitlab.call_gitlab_app_webhook_for_feature_state",
    )
    resource = FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/10",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )
    # Reset mock to ignore the after_save call
    mock_call_task.delay.reset_mock()

    # When
    resource.delete()

    # Then
    mock_call_task.delay.assert_called_once()


@pytest.mark.django_db
def test_execute_before_save_actions__gitlab_delete_no_config__returns_early(
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given - no gitlab config
    mock_call_task = mocker.patch(
        "integrations.gitlab.gitlab.call_gitlab_app_webhook_for_feature_state",
    )
    resource = FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/10",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )
    mock_call_task.delay.reset_mock()

    # When
    resource.delete()

    # Then
    mock_call_task.delay.assert_not_called()


# ---------------------------------------------------------------
# Feature.create_github_comment - GitLab branch tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_feature_create_github_comment__with_gitlab_config__calls_gitlab_task(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/1",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )
    mock_call_task = mocker.patch(
        "integrations.gitlab.gitlab.call_gitlab_app_webhook_for_feature_state",
    )

    # When - soft delete the feature
    feature.delete()

    # Then
    mock_call_task.delay.assert_called_once()


# ---------------------------------------------------------------
# FeatureSegment.create_github_comment - GitLab branch tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_feature_segment_create_github_comment__with_gitlab_config__calls_gitlab_task(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    environment: Any,
    mocker: MockerFixture,
) -> None:
    # Given
    from features.models import FeatureSegment
    from segments.models import Segment

    mock_call_task = mocker.patch(
        "integrations.gitlab.gitlab.call_gitlab_app_webhook_for_feature_state",
    )
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/1",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )

    segment = Segment.objects.create(name="test_segment", project=feature.project)
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment,
    )
    mock_call_task.delay.reset_mock()

    # When
    feature_segment.delete()

    # Then
    mock_call_task.delay.assert_called_once()


# ---------------------------------------------------------------
# tag_feature_per_gitlab_event — work_items URL → issues variant (line 74)
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_tag_feature_per_gitlab_event__reverse_work_items_variant__finds_feature(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given — feature is stored under an /-/issues/ URL, but the webhook sends /-/work_items/
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    issues_url = "https://gitlab.example.com/testgroup/testrepo/-/issues/9"
    FeatureExternalResource.objects.create(
        url=issues_url,
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )
    work_items_url = "https://gitlab.example.com/testgroup/testrepo/-/work_items/9"

    # When
    tag_feature_per_gitlab_event(
        event_type="issue",
        action="close",
        metadata={"web_url": work_items_url},
        project_path="testgroup/testrepo",
    )

    # Then
    feature.refresh_from_db()
    from integrations.gitlab.constants import GitLabTag

    tag_labels = list(feature.tags.values_list("label", flat=True))
    assert GitLabTag.ISSUE_CLOSED.value in tag_labels


# ---------------------------------------------------------------
# generate_data — non-removed event populates env fields (lines 221, 236)
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_generate_data__non_removed_event_with_segment_feature_state__includes_env_and_segment_name(
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    environment: Any,
    segment: Any,
    mocker: MockerFixture,
) -> None:
    # Given
    from features.models import FeatureSegment, FeatureState

    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment,
    )
    feature_state = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        enabled=True,
    )

    # When
    result = generate_data(
        gitlab_configuration=gitlab_configuration,
        feature=feature,
        type=GitLabEventType.FLAG_UPDATED.value,
        feature_states=[feature_state],
    )

    # Then
    assert len(result.feature_states) == 1
    fs_data = result.feature_states[0]
    # Lines 224-231: environment fields are populated for non-removed event
    assert "environment_name" in fs_data
    assert "enabled" in fs_data
    assert "last_updated" in fs_data
    assert "environment_api_key" in fs_data
    # Line 236: segment_name is extracted from feature_segment
    assert fs_data.get("segment_name") == segment.name


# ---------------------------------------------------------------
# _post_to_resource — successful IID and project_path extraction (lines 61, 68)
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_post_to_resource__issue_url__extracts_iid_and_project_path(
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_post_comment = mocker.patch("integrations.gitlab.tasks.post_comment_to_gitlab")
    # testgroup/testrepo matches the gitlab_configuration fixture's project_name
    resource_url = "https://gitlab.example.com/testgroup/testrepo/-/issues/42"

    # When
    _post_to_resource(
        resource_url=resource_url,
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        body="Comment body",
    )

    # Then — lines 61 and 68: resource_iid and project_path were successfully extracted
    mock_post_comment.assert_called_once_with(
        instance_url="https://gitlab.example.com",
        access_token="test-token",
        gitlab_project_id=gitlab_configuration.gitlab_project_id,
        resource_type="issues",
        resource_iid=42,
        body="Comment body",
    )

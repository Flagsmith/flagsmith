import json
from textwrap import dedent

import pytest
import responses
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.models import Environment
from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.services.comments import (
    post_linked_comment,
    post_unlinked_comment,
)


@pytest.fixture(autouse=True)
def _mock_site_url(mocker: MockerFixture) -> None:
    mocker.patch(
        "integrations.gitlab.services.comments.get_current_site_url",
        return_value="https://app.flagsmith.example.com",
    )


@pytest.mark.parametrize(
    "resource_type, url_path, iid",
    [
        (ResourceType.GITLAB_ISSUE, "issues/42", 42),
        (ResourceType.GITLAB_MR, "merge_requests/7", 7),
    ],
    ids=["issue", "merge_request"],
)
@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__valid_resource__posts_note_and_logs(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    environment: Environment,
    log: StructuredLogCapture,
    resource_type: ResourceType,
    url_path: str,
    iid: int,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        url=f"https://gitlab.example.com/testorg/testrepo/-/{url_path}",
        type=resource_type.value,
        feature=feature,
    )
    responses.post(
        f"https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/{url_path}/notes",
        json={"id": 1},
        status=201,
    )

    # When
    post_linked_comment(resource)

    # Then
    [call] = responses.calls
    assert json.loads(call.request.body)["body"] == dedent(f"""\
        :link: Linked to Flagsmith feature flag `{feature.name}`

        | Environment | Enabled | Value |
        | :--- | :----- | :------ |
        | [{environment.name}](https://app.flagsmith.example.com/project/{feature.project_id}/environment/{environment.api_key}/features?feature={feature.id}) | :x: Disabled |  |

        Segment and identity overrides may apply -- check each environment above for details.
        """)

    assert log.events == [
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": gitlab_config.project.organisation_id,
            "project__id": gitlab_config.project_id,
            "feature__id": feature.id,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": iid,
        },
    ]


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__api_error__logs_warning_does_not_raise(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    environment: Environment,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        status=500,
    )

    # When
    post_linked_comment(resource)

    # Then
    assert log.events == [
        {
            "level": "warning",
            "event": "comment.post_failed",
            "organisation__id": gitlab_config.project.organisation_id,
            "project__id": gitlab_config.project_id,
            "feature__id": feature.id,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 42,
            "exc_info": mocker.ANY,
        },
    ]


@pytest.mark.django_db
def test_post_linked_comment__no_config__returns_early(
    feature: Feature,
    log: StructuredLogCapture,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )

    # When
    post_linked_comment(resource)

    # Then
    assert log.events == []


@pytest.mark.parametrize(
    "resource_type, url_path, iid",
    [
        (ResourceType.GITLAB_ISSUE, "issues/42", 42),
        (ResourceType.GITLAB_MR, "merge_requests/7", 7),
    ],
    ids=["issue", "merge_request"],
)
@pytest.mark.django_db
@responses.activate
def test_post_unlinked_comment__valid_resource__posts_note_and_logs(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    log: StructuredLogCapture,
    resource_type: ResourceType,
    url_path: str,
    iid: int,
) -> None:
    # Given
    responses.post(
        f"https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/{url_path}/notes",
        json={"id": 1},
        status=201,
    )

    # When
    post_unlinked_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        resource_url=f"https://gitlab.example.com/testorg/testrepo/-/{url_path}",
        resource_type=resource_type,
        project_id=feature.project_id,
    )

    # Then
    [call] = responses.calls
    assert json.loads(call.request.body)["body"] == dedent(f"""\
        Unlinked from Flagsmith feature flag `{feature.name}`
        """)

    assert log.events == [
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": gitlab_config.project.organisation_id,
            "project__id": gitlab_config.project_id,
            "feature__id": feature.id,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": iid,
        },
    ]


@pytest.mark.django_db
def test_post_unlinked_comment__no_config__returns_early(
    feature: Feature,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    post_unlinked_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        resource_url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        resource_type=ResourceType.GITLAB_ISSUE,
        project_id=feature.project_id,
    )

    # Then
    assert log.events == []

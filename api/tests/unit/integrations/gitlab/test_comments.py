import json
from textwrap import dedent

import pytest
import responses
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.identities.models import Identity
from environments.models import Environment
from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature, FeatureSegment, FeatureState
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.services.comments import (
    _post_note_to_resource,
    post_feature_deleted_comment,
    post_linked_comment,
    post_state_change_comment,
    post_unlinked_comment,
)
from segments.models import Segment


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
        ⛓️‍💥 Unlinked from Flagsmith feature flag `{feature.name}`
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


@pytest.mark.parametrize(
    "scope, expected_body_fragment",
    [
        ("environment", "in **Test Environment**: :x: Disabled\n"),
        (
            "segment",
            "in **Test Environment** for segment **segment**: :x: Disabled\n",
        ),
        (
            "identity",
            "in **Test Environment** for identity **test_identity**: :x: Disabled\n",
        ),
    ],
    ids=["environment", "segment", "identity"],
)
@pytest.mark.django_db
@responses.activate
def test_post_state_change_comment__all_scopes__posts_note_with_correct_body(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    environment: Environment,
    segment: Segment,
    identity: Identity,
    log: StructuredLogCapture,
    scope: str,
    expected_body_fragment: str,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        json={"id": 1},
        status=201,
    )

    if scope == "environment":
        feature_state = FeatureState.objects.get(
            feature=feature,
            environment=environment,
            feature_segment__isnull=True,
            identity__isnull=True,
        )
    elif scope == "segment":
        feature_segment = FeatureSegment.objects.create(
            feature=feature,
            segment=segment,
            environment=environment,
        )
        feature_state = FeatureState.objects.create(
            feature=feature,
            environment=environment,
            feature_segment=feature_segment,
        )
    else:
        feature_state = FeatureState.objects.create(
            feature=feature,
            environment=environment,
            identity=identity,
        )

    # When
    post_state_change_comment(feature_state)

    # Then
    [call] = responses.calls
    body = json.loads(call.request.body)["body"]
    assert body == f"Feature flag `{feature.name}` {expected_body_fragment}"

    assert log.events == [
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": gitlab_config.project.organisation_id,
            "project__id": gitlab_config.project_id,
            "feature__id": feature.id,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 42,
        },
    ]


@pytest.mark.django_db
def test_post_state_change_comment__no_config__returns_early(
    feature: Feature,
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        feature_segment__isnull=True,
        identity__isnull=True,
    )

    # When
    post_state_change_comment(feature_state)

    # Then
    assert log.events == []


@pytest.mark.django_db
def test_post_state_change_comment__no_linked_resources__returns_early(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        feature_segment__isnull=True,
        identity__isnull=True,
    )

    # When
    post_state_change_comment(feature_state)

    # Then
    assert log.events == []


@pytest.mark.django_db
@responses.activate
def test_post_state_change_comment__api_error__logs_warning(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    environment: Environment,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        status=500,
    )
    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        feature_segment__isnull=True,
        identity__isnull=True,
    )

    # When
    post_state_change_comment(feature_state)

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
@responses.activate
def test_post_state_change_comment__multiple_resources__posts_to_all(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/merge_requests/2",
        type=ResourceType.GITLAB_MR.value,
        feature=feature,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/1/notes",
        json={"id": 1},
        status=201,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/merge_requests/2/notes",
        json={"id": 2},
        status=201,
    )
    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        feature_segment__isnull=True,
        identity__isnull=True,
    )

    # When
    post_state_change_comment(feature_state)

    # Then
    assert len(responses.calls) == 2
    assert log.events == [
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": gitlab_config.project.organisation_id,
            "project__id": gitlab_config.project_id,
            "feature__id": feature.id,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 1,
        },
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": gitlab_config.project.organisation_id,
            "project__id": gitlab_config.project_id,
            "feature__id": feature.id,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 2,
        },
    ]


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
def test_post_feature_deleted_comment__valid_resources__posts_note_and_logs(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    log: StructuredLogCapture,
    resource_type: ResourceType,
    url_path: str,
    iid: int,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
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
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    [call] = responses.calls
    assert json.loads(call.request.body)["body"] == dedent(f"""\
        Feature flag `{feature.name}` was deleted
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
def test_post_feature_deleted_comment__no_config__returns_early(
    feature: Feature,
    log: StructuredLogCapture,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )

    # When
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    assert log.events == []


@pytest.mark.django_db
def test_post_feature_deleted_comment__no_gitlab_resources__returns_early(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    assert log.events == []


@pytest.mark.django_db
@responses.activate
def test_post_feature_deleted_comment__api_error__logs_warning(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        status=500,
    )

    # When
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

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
@responses.activate
def test_post_feature_deleted_comment__multiple_resources__posts_to_all(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    log: StructuredLogCapture,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/merge_requests/7",
        type=ResourceType.GITLAB_MR.value,
        feature=feature,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        json={"id": 1},
        status=201,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/merge_requests/7/notes",
        json={"id": 2},
        status=201,
    )

    # When
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    assert len(responses.calls) == 2
    for call in responses.calls:
        assert json.loads(call.request.body)["body"] == dedent(f"""\
            Feature flag `{feature.name}` was deleted
            """)

    assert log.events == [
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": gitlab_config.project.organisation_id,
            "project__id": gitlab_config.project_id,
            "feature__id": feature.id,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 42,
        },
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": gitlab_config.project.organisation_id,
            "project__id": gitlab_config.project_id,
            "feature__id": feature.id,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 7,
        },
    ]


@pytest.mark.parametrize(
    "bad_url",
    [
        "https://gitlab.example.com/not-a-resource",
        "",
    ],
    ids=["no_path_match", "empty_url"],
)
@pytest.mark.django_db
def test_post_note_to_resource__unparseable_url__returns_early(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    log: StructuredLogCapture,
    bad_url: str,
) -> None:
    # Given / When
    _post_note_to_resource(
        config=gitlab_config,
        resource_url=bad_url,
        resource_type=ResourceType.GITLAB_ISSUE.value,
        feature_id=feature.id,
        body="test",
    )

    # Then
    assert log.events == []


@pytest.mark.django_db
def test_post_note_to_resource__unrecognised_resource_type__returns_early(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    _post_note_to_resource(
        config=gitlab_config,
        resource_url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        resource_type="UNKNOWN_TYPE",
        feature_id=feature.id,
        body="test",
    )

    # Then
    assert log.events == []


@pytest.mark.django_db
def test_post_state_change_comment__no_environment__returns_early(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )
    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        feature_segment__isnull=True,
        identity__isnull=True,
    )
    # Simulate a feature state with no environment by clearing
    # the cached relation without touching the database.
    feature_state.environment = None

    # When
    post_state_change_comment(feature_state)

    # Then
    assert log.events == []


@pytest.mark.django_db
@responses.activate
def test_post_state_change_comment__enabled_with_value__renders_value_in_body(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/42",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        json={"id": 1},
        status=201,
    )
    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        feature_segment__isnull=True,
        identity__isnull=True,
    )
    feature_state.enabled = True
    feature_state.save()
    feature_state.feature_state_value.string_value = "my_value"
    feature_state.feature_state_value.save()

    # When
    post_state_change_comment(feature_state)

    # Then
    [call] = responses.calls
    body = json.loads(call.request.body)["body"]
    assert body == (
        f"Feature flag `{feature.name}` "
        f"in **{environment.name}**: "
        f":white_check_mark: Enabled, value `my_value`\n"
    )

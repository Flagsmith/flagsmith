from datetime import datetime
from unittest.mock import MagicMock

import pytest
import responses
import simplejson as json  # type: ignore[import-untyped]
from common.environments.permissions import (
    UPDATE_FEATURE_STATE,
)
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils.formats import get_format
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature, FeatureSegment, FeatureState
from features.serializers import (
    FeatureStateSerializerBasic,
    WritableNestedFeatureStateSerializer,
)
from features.versioning.models import EnvironmentFeatureVersion
from integrations.github.constants import GITHUB_API_URL, GITHUB_API_VERSION
from integrations.github.models import GithubConfiguration, GitHubRepository
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Segment
from tests.types import WithEnvironmentPermissionsCallable
from users.models import FFAdminUser

_django_json_encoder_default = DjangoJSONEncoder().default


def expected_default_body(
    project_id: str,
    environment_api_key: str,
    feature_id: str,
    feature_state_updated_at: str,
    feature_state_enabled: str = "❌ Disabled",
    feature_state_value: str = "`value`",
) -> str:
    return (
        "| Environment | Enabled | Value | Last Updated (UTC) |\n"
        "| :--- | :----- | :------ | :------ |\n"
        f"| [Test Environment](https://example.com/project/{project_id}/"
        f"environment/{environment_api_key}/features?feature={feature_id}&tab=value) "
        f"| {feature_state_enabled} | {feature_state_value} | {feature_state_updated_at} |\n"
    )


def expected_segment_comment_body(
    project_id: str,
    environment_api_key: str,
    feature_id: str,
    segment_override_updated_at: str,
    segment_override_enabled: str,
    segment_override_value: str,
) -> str:
    return (
        "Segment `segment` values:\n"
        "| Environment | Enabled | Value | Last Updated (UTC) |\n"
        "| :--- | :----- | :------ | :------ |\n"
        f"| [Test Environment](https://example.com/project/{project_id}/"
        f"environment/{environment_api_key}/features?feature={feature_id}&tab=segment-overrides) "
        f"| {segment_override_enabled} | {segment_override_value} | {segment_override_updated_at} |\n"
    )


@responses.activate
def test_create_feature_external_resource(
    admin_client_new: APIClient,
    feature_with_value: Feature,
    segment_override_for_feature_with_value: FeatureState,
    environment: Environment,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    post_request_mock: MagicMock,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    repository_owner_name = (
        f"{github_repository.repository_owner}/{github_repository.repository_name}"
    )
    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": f"https://github.com/{repository_owner_name}/issues/35",
        "feature": feature_with_value.id,
        "metadata": {"state": "open"},
    }

    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature_with_value.id},
    )

    # When
    response = admin_client_new.post(
        url, data=feature_external_resource_data, format="json"
    )

    # Then
    feature_state_update_at = (
        FeatureState.objects.filter(feature=feature_with_value)
        .first()
        .updated_at.strftime(get_format("DATETIME_INPUT_FORMATS")[0])
    )
    segment_override_updated_at = FeatureState.objects.get(
        id=segment_override_for_feature_with_value.id
    ).updated_at.strftime(get_format("DATETIME_INPUT_FORMATS")[0])

    expected_comment_body = (
        "**Flagsmith feature linked:** `feature_with_value`\n"
        + "Default Values:\n"
        + expected_default_body(
            project.id,  # type: ignore[arg-type]
            environment.api_key,
            feature_with_value.id,  # type: ignore[arg-type]
            feature_state_update_at,
        )
        + "\n"
        + expected_segment_comment_body(
            project.id,  # type: ignore[arg-type]
            environment.api_key,
            feature_with_value.id,  # type: ignore[arg-type]
            segment_override_updated_at,
            "❌ Disabled",
            "`value`",
        )
    )
    post_request_mock.assert_called_with(
        f"https://api.github.com/repos/{repository_owner_name}/issues/35/comments",
        json={"body": f"{expected_comment_body}"},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )
    assert response.status_code == status.HTTP_201_CREATED
    # assert that the payload has been save to the database
    feature_external_resources = FeatureExternalResource.objects.filter(
        feature=feature_with_value,
        type=feature_external_resource_data["type"],
        url=feature_external_resource_data["url"],
    ).all()
    assert len(feature_external_resources) == 1
    assert feature_external_resources[0].metadata == json.dumps(
        feature_external_resource_data["metadata"], default=_django_json_encoder_default
    )
    assert feature_external_resources[0].feature == feature_with_value
    assert feature_external_resources[0].type == feature_external_resource_data["type"]
    assert feature_external_resources[0].url == feature_external_resource_data["url"]

    # And When
    responses.add(
        method="GET",
        url=f"{GITHUB_API_URL}repos/{repository_owner_name}/issues/35",
        status=200,
        json={"title": "resource name", "state": "open"},
    )
    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature_with_value.id},
    )

    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert (
        response.json()["results"][0]["type"] == feature_external_resource_data["type"]
    )
    assert response.json()["results"][0]["url"] == feature_external_resource_data["url"]
    feature_external_resource_data["metadata"]["title"] = "resource name"  # type: ignore[index]

    assert (
        response.json()["results"][0]["metadata"]
        == feature_external_resource_data["metadata"]
    )


@responses.activate
def test_create_feature_external_resource_missing_tags(
    admin_client_new: APIClient,
    feature_with_value: Feature,
    segment_override_for_feature_with_value: FeatureState,
    environment: Environment,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    post_request_mock: MagicMock,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    Tag.objects.all().delete()
    repository_owner_name = (
        f"{github_repository.repository_owner}/{github_repository.repository_name}"
    )
    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": f"https://github.com/{repository_owner_name}/issues/35",
        "feature": feature_with_value.id,
        "metadata": {"state": "open"},
    }

    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature_with_value.id},
    )

    # When
    response = admin_client_new.post(
        url, data=feature_external_resource_data, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert Tag.objects.count() == 1
    tag = Tag.objects.first()
    assert tag.project == project  # type: ignore[union-attr]
    assert tag.label == "Issue Open"  # type: ignore[union-attr]


def test_cannot_create_feature_external_resource_with_an_invalid_gh_url(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": "https://github.com/repoowner/repo-name/pull/1",
        "feature": feature.id,
        "metadata": {"state": "open"},
    }

    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature.id},
    )

    # When
    response = admin_client_new.post(
        url, data=feature_external_resource_data, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid GitHub Issue/PR URL"


def test_cannot_create_feature_external_resource_with_an_incorrect_gh_type(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "GITHUB_INCORRECT_TYPE",
        "url": "https://github.com/repoowner/repo-name/pull/1",
        "feature": feature.id,
        "metadata": {"state": "open"},
    }

    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature.id},
    )

    # When
    response = admin_client_new.post(
        url, data=feature_external_resource_data, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Incorrect GitHub type"


def test_cannot_create_feature_external_resource_when_doesnt_have_a_valid_github_integration(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": "https://example.com?item=create",
        "feature": feature.id,
        "metadata": {"status": "open"},
    }
    url = reverse(
        "api-v1:projects:feature-external-resources-list", args=[project.id, feature.id]
    )

    # When
    response = admin_client_new.post(
        url, data=feature_external_resource_data, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_cannot_create_feature_external_resource_when_doesnt_have_permissions(
    admin_client_new: APIClient,
    feature: Feature,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": "https://example.com?item=create",
        "feature": feature.id,
        "metadata": {"status": "open"},
    }
    url = reverse(
        "api-v1:projects:feature-external-resources-list", args=[2, feature.id]
    )

    # When
    response = admin_client_new.post(
        url, data=feature_external_resource_data, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_cannot_create_feature_external_resource_when_the_type_is_incorrect(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "UNKNOWN_TYPE",
        "url": "https://example.com",
        "feature": feature.id,
    }
    url = reverse(
        "api-v1:projects:feature-external-resources-list", args=[project.id, feature.id]
    )

    # When
    response = admin_client_new.post(url, data=feature_external_resource_data)
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_cannot_create_feature_external_resource_due_to_unique_constraint(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    feature_external_resource: FeatureExternalResource,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": "https://github.com/repositoryownertest/repositorynametest/issues/11",
        "feature": feature.id,
    }
    url = reverse(
        "api-v1:projects:feature-external-resources-list", args=[project.id, feature.id]
    )

    # When
    response = admin_client_new.post(url, data=feature_external_resource_data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["non_field_errors"][0]
        == "The fields feature, url must make a unique set."
    )


def test_update_feature_external_resource(
    admin_client_new: APIClient,
    feature: Feature,
    feature_external_resource: FeatureExternalResource,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    post_request_mock: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": f"https://github.com/{github_repository.repository_owner}/{github_repository.repository_name}/issues/12",
        "feature": feature.id,
        "metadata": '{"state": "open"}',
    }
    url = reverse(
        "api-v1:projects:feature-external-resources-detail",
        args=[project.id, feature.id, feature_external_resource.id],
    )
    # When
    response = admin_client_new.put(url, data=feature_external_resource_data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["url"] == feature_external_resource_data["url"]


def test_delete_feature_external_resource(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    feature_external_resource: FeatureExternalResource,
    post_request_mock: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:feature-external-resources-detail",
        args=[project.id, feature.id, feature_external_resource.id],
    )

    # When
    response = admin_client_new.delete(url)

    # Then
    post_request_mock.assert_called_with(
        "https://api.github.com/repos/repositoryownertest/repositorynametest/issues/11/comments",
        json={
            "body": "**The feature flag `Test Feature1` was unlinked from the issue/PR**"
        },
        headers={
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FeatureExternalResource.objects.filter(
        id=feature_external_resource.id
    ).exists()


@responses.activate
def test_get_feature_external_resources(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    feature_external_resource: FeatureExternalResource,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature.id},
    )

    responses.add(
        method="GET",
        url=f"{GITHUB_API_URL}repos/repositoryownertest/repositorynametest/issues/11",
        status=200,
        json={"title": "resource name", "state": "open"},
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_get_feature_external_resource(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    feature_external_resource: FeatureExternalResource,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:feature-external-resources-detail",
        args=[project.id, feature.id, feature_external_resource.id],
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == feature_external_resource.id
    assert response.data["type"] == feature_external_resource.type
    assert response.data["url"] == feature_external_resource.url


def test_create_github_comment_on_feature_state_updated(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    post_request_mock: MagicMock,
    mocker: MockerFixture,
    environment: Environment,
    feature_external_resource: FeatureExternalResource,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE], environment.id, False)
    feature_state = FeatureState.objects.get(
        feature=feature, environment=environment.id
    )

    payload = dict(FeatureStateSerializerBasic(instance=feature_state).data)

    payload["enabled"] = not feature_state.enabled
    url = reverse(
        viewname="api-v1:environments:environment-featurestates-detail",
        kwargs={"environment_api_key": environment.api_key, "pk": feature_state.id},
    )

    # When
    response = staff_client.put(path=url, data=payload, format="json")

    # Then
    feature_state_updated_at = FeatureState.objects.get(
        id=feature_state.id
    ).updated_at.strftime(get_format("DATETIME_INPUT_FORMATS")[0])

    expected_body_comment = (
        "**Flagsmith Feature `Test Feature1` has been updated:**\n"
        + expected_default_body(
            project.id,  # type: ignore[arg-type]
            environment.api_key,
            feature.id,  # type: ignore[arg-type]
            feature_state_updated_at,
            "✅ Enabled",
            "",
        )
    )

    assert response.status_code == status.HTTP_200_OK

    post_request_mock.assert_called_with(
        "https://api.github.com/repos/repositoryownertest/repositorynametest/issues/11/comments",
        json={"body": expected_body_comment},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


def test_create_github_comment_on_feature_was_deleted(
    admin_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    feature_external_resource: FeatureExternalResource,
    post_request_mock: MagicMock,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    url = reverse(
        viewname="api-v1:projects:project-features-detail",
        kwargs={"project_pk": project.id, "pk": feature.id},
    )

    # When
    response = admin_client.delete(path=url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    post_request_mock.assert_called_with(
        "https://api.github.com/repos/repositoryownertest/repositorynametest/issues/11/comments",
        json={"body": "**The Feature Flag `Test Feature1` was deleted**"},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


def test_create_github_comment_on_segment_override_updated(
    feature_with_value: Feature,
    segment_override_for_feature_with_value: FeatureState,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    post_request_mock: MagicMock,
    environment: Environment,
    admin_client: APIClient,
    feature_with_value_external_resource: FeatureExternalResource,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    feature_state = segment_override_for_feature_with_value
    payload = dict(WritableNestedFeatureStateSerializer(instance=feature_state).data)

    payload["enabled"] = not feature_state.enabled
    payload["feature_state_value"]["string_value"] = "new value"

    url = reverse(
        viewname="api-v1:features:featurestates-detail",
        kwargs={"pk": feature_state.id},
    )

    # When
    response = admin_client.put(path=url, data=payload, format="json")

    # Then
    segment_override_updated_at = FeatureState.objects.get(
        id=segment_override_for_feature_with_value.id
    ).updated_at.strftime(get_format("DATETIME_INPUT_FORMATS")[0])

    expected_comment_body = (
        "**Flagsmith Feature `feature_with_value` has been updated:**\n"
        + "\n"
        + expected_segment_comment_body(
            project.id,  # type: ignore[arg-type]
            environment.api_key,
            feature_with_value.id,  # type: ignore[arg-type]
            segment_override_updated_at,
            "✅ Enabled",
            "`new value`",
        )
    )

    assert response.status_code == status.HTTP_200_OK

    post_request_mock.assert_called_with(
        "https://api.github.com/repos/repositoryownertest/repositorynametest/issues/11/comments",
        json={"body": expected_comment_body},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


def test_create_github_comment_on_segment_override_deleted(
    segment_override_for_feature_with_value: FeatureState,
    feature_with_value_segment: FeatureSegment,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    post_request_mock: MagicMock,
    admin_client_new: APIClient,
    feature_with_value_external_resource: FeatureExternalResource,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    url = reverse(
        viewname="api-v1:features:feature-segment-detail",
        kwargs={"pk": feature_with_value_segment.id},
    )

    # When
    response = admin_client_new.delete(path=url, format="json")

    # Then

    assert response.status_code == status.HTTP_204_NO_CONTENT

    post_request_mock.assert_called_with(
        "https://api.github.com/repos/repositoryownertest/repositorynametest/issues/11/comments",
        json={
            "body": "**The Segment Override `segment` for Feature Flag `feature_with_value` was deleted**"
        },
        headers={
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


def test_create_github_comment_using_v2(
    admin_client_new: APIClient,
    environment_v2_versioning: Environment,
    segment: Segment,
    feature: Feature,
    environment: Environment,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    feature_external_resource: FeatureExternalResource,
    post_request_mock: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-list",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
        ],
    )

    data = {
        "feature_segment": {"segment": segment.id},
        "enabled": True,
        "feature_state_value": {
            "string_value": "segment value!",
        },
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    response_data = response.json()

    # Then
    format = "%Y-%m-%dT%H:%M:%S.%fZ"
    formatted_updated_at = datetime.strptime(
        response_data["updated_at"], format
    ).strftime(get_format("DATETIME_INPUT_FORMATS")[0])
    expected_comment_body = (
        "**Flagsmith Feature `Test Feature1` has been updated:**\n"
        + "\n"
        + expected_segment_comment_body(
            project.id,  # type: ignore[arg-type]
            environment.api_key,
            feature.id,  # type: ignore[arg-type]
            formatted_updated_at,
            "✅ Enabled",
            "`segment value!`",
        )
    )

    post_request_mock.assert_called_with(
        "https://api.github.com/repos/repositoryownertest/repositorynametest/issues/11/comments",
        json={"body": expected_comment_body},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )

    assert response.status_code == status.HTTP_201_CREATED


def test_create_github_comment_using_v2_fails_on_wrong_params(
    admin_client_new: APIClient,
    environment_v2_versioning: Environment,
    segment: Segment,
    feature: Feature,
    environment: Environment,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    feature_external_resource: FeatureExternalResource,
    post_request_mock: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    url = reverse(
        "api-v1:versioning:environment-feature-version-featurestates-list",
        args=[
            environment_v2_versioning.id,
            feature.id,
            environment_feature_version.uuid,
        ],
    )

    data = {
        "feature_segment": {"segment": segment.id},
        "enabled": True,
        "feature_state_value": {
            "string_value": {"value": "wrong structure"},
        },
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@responses.activate
@pytest.mark.freeze_time("2024-05-28T09:09:47.325132+00:00")
def test_create_feature_external_resource_on_environment_with_v2(
    admin_client_new: APIClient,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    segment_override_for_feature_with_value: FeatureState,
    environment_v2_versioning: Environment,
    post_request_mock: MagicMock,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    feature_id = segment_override_for_feature_with_value.feature_id
    repository_owner_name = (
        f"{github_repository.repository_owner}/{github_repository.repository_name}"
    )

    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": f"https://github.com/{repository_owner_name}/issues/35",
        "feature": feature_id,
        "metadata": {"state": "open"},
    }

    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature_id},
    )

    # When
    response = admin_client_new.post(
        url, data=feature_external_resource_data, format="json"
    )

    # Then
    feature_state_update_at = FeatureState.objects.get(
        id=segment_override_for_feature_with_value.id
    ).updated_at.strftime(get_format("DATETIME_INPUT_FORMATS")[0])

    segment_override_updated_at = FeatureState.objects.get(
        id=segment_override_for_feature_with_value.id
    ).updated_at.strftime(get_format("DATETIME_INPUT_FORMATS")[0])

    expected_comment_body = (
        "**Flagsmith feature linked:** `feature_with_value`\n"
        + "Default Values:\n"
        + expected_default_body(
            project.id,  # type: ignore[arg-type]
            environment_v2_versioning.api_key,
            feature_id,  # type: ignore[arg-type]
            feature_state_update_at,
        )
        + "\n"
        + expected_segment_comment_body(
            project.id,  # type: ignore[arg-type]
            environment_v2_versioning.api_key,
            feature_id,  # type: ignore[arg-type]
            segment_override_updated_at,
            "❌ Disabled",
            "`value`",
        )
    )

    assert response.status_code == status.HTTP_201_CREATED

    post_request_mock.assert_called_with(
        f"https://api.github.com/repos/{repository_owner_name}/issues/35/comments",
        json={"body": f"{expected_comment_body}"},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


def test_cannot_create_feature_external_resource_for_the_same_feature_and_resource_uri(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    feature_external_resource_gh_pr: FeatureExternalResource,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "GITHUB_PR",
        "url": "https://github.com/repositoryownertest/repositorynametest/pull/1",
        "feature": feature.id,
        "metadata": {"state": "open"},
    }

    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature.id},
    )

    # When
    response = admin_client_new.post(
        url, data=feature_external_resource_data, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["non_field_errors"][0]
        == "The fields feature, url must make a unique set."
    )

import simplejson as json
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils.formats import get_format
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from environments.permissions.constants import UPDATE_FEATURE_STATE
from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature, FeatureState
from features.serializers import (
    FeatureStateSerializerBasic,
    WritableNestedFeatureStateSerializer,
)
from integrations.github.models import GithubConfiguration, GithubRepository
from projects.models import Project
from tests.types import WithEnvironmentPermissionsCallable

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


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def raise_for_status(self) -> None:
            pass

        def json(self):
            return self.json_data

    return MockResponse(json_data={"data": "data"}, status_code=200)


def test_create_feature_external_resource(
    admin_client_new: APIClient,
    feature_with_value: Feature,
    segment_featurestate_and_feature_with_value: FeatureState,
    environment: Environment,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.github.generate_token",
    )

    mock_generate_token.return_value = "mocked_token"
    github_request_mock = mocker.patch(
        "requests.post", side_effect=mocked_requests_post
    )

    feature_state = FeatureState.objects.filter(feature=feature_with_value).first()
    feature_state_updated_at = feature_state.updated_at.strftime(
        get_format("DATETIME_INPUT_FORMATS")[0]
    )
    segment_override_updated_at = (
        segment_featurestate_and_feature_with_value.updated_at.strftime(
            get_format("DATETIME_INPUT_FORMATS")[0]
        )
    )

    expected_comment_body = (
        "**Flagsmith feature linked:** `feature_with_value`\n"
        + "Default Values:\n"
        + expected_default_body(
            project.id,
            environment.api_key,
            feature_with_value.id,
            feature_state_updated_at,
        )
        + "\n"
        + expected_segment_comment_body(
            project.id,
            environment.api_key,
            feature_with_value.id,
            segment_override_updated_at,
            "❌ Disabled",
            "`value`",
        )
    )

    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": "https://github.com/repoowner/repo-name/issues/35",
        "feature": feature_with_value.id,
        "metadata": {"status": "open"},
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
    github_request_mock.assert_called_with(
        "https://api.github.com/repos/repoowner/repo-name/issues/35/comments",
        json={"body": f"{expected_comment_body}"},
        headers={
            "Accept": "application/vnd.github.v3+json",
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
    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature_with_value.id},
    )

    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert (
        response.json()["results"][0]["type"] == feature_external_resource_data["type"]
    )
    assert response.json()["results"][0]["url"] == feature_external_resource_data["url"]
    assert (
        response.json()["results"][0]["metadata"]
        == feature_external_resource_data["metadata"]
    )


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
    feature_external_resource: FeatureExternalResource,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": "https://github.com/userexample/example-project-repo/issues/11",
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
        "Duplication error. The feature already has this resource URI"
        in response.json()[0]
    )


def test_delete_feature_external_resource(
    admin_client_new: APIClient,
    feature_external_resource: FeatureExternalResource,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.github.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
    github_request_mock = mocker.patch(
        "requests.post", side_effect=mocked_requests_post
    )
    url = reverse(
        "api-v1:projects:feature-external-resources-detail",
        args=[project.id, feature.id, feature_external_resource.id],
    )

    # When
    response = admin_client_new.delete(url)

    # Then
    github_request_mock.assert_called_with(
        "https://api.github.com/repos/userexample/example-project-repo/issues/11/comments",
        json={
            "body": "### The feature flag `Test Feature1` was unlinked from the issue/PR"
        },
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FeatureExternalResource.objects.filter(
        id=feature_external_resource.id
    ).exists()


def test_get_feature_external_resources(
    admin_client_new: APIClient,
    feature_external_resource: FeatureExternalResource,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature.id},
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_get_feature_external_resource(
    admin_client_new: APIClient,
    feature_external_resource: FeatureExternalResource,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
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
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    feature_external_resource: FeatureExternalResource,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker: MockerFixture,
    environment: Environment,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])
    feature_state = FeatureState.objects.get(
        feature=feature, environment=environment.id
    )
    mock_generate_token = mocker.patch(
        "integrations.github.github.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
    github_request_mock = mocker.patch(
        "requests.post", side_effect=mocked_requests_post
    )

    feature_state_updated_at = feature_state.updated_at.strftime(
        get_format("DATETIME_INPUT_FORMATS")[0]
    )

    expected_body_comment = (
        "Flagsmith Feature `Test Feature1` has been updated:\n"
        + expected_default_body(
            project.id,
            environment.api_key,
            feature.id,
            feature_state_updated_at,
            "✅ Enabled",
            "",
        )
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
    assert response.status_code == status.HTTP_200_OK

    github_request_mock.assert_called_with(
        "https://api.github.com/repos/userexample/example-project-repo/issues/11/comments",
        json={"body": expected_body_comment},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


def test_create_github_comment_on_feature_was_deleted(
    admin_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    feature_external_resource: FeatureExternalResource,
    feature: Feature,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.github.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"

    github_request_mock = mocker.patch(
        "requests.post", side_effect=mocked_requests_post
    )

    url = reverse(
        viewname="api-v1:projects:project-features-detail",
        kwargs={"project_pk": project.id, "pk": feature.id},
    )

    # When
    response = admin_client.delete(path=url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    github_request_mock.assert_called_with(
        "https://api.github.com/repos/userexample/example-project-repo/issues/11/comments",
        json={"body": "### The Feature Flag `Test Feature1` was deleted"},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


def test_create_github_comment_on_segment_override_updated(
    feature_with_value: Feature,
    segment_featurestate_and_feature_with_value: FeatureState,
    feature_with_value_external_resource: FeatureExternalResource,
    project: Project,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker: MockerFixture,
    environment: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    feature_state = segment_featurestate_and_feature_with_value
    mock_generate_token = mocker.patch(
        "integrations.github.github.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
    github_request_mock = mocker.patch(
        "requests.post", side_effect=mocked_requests_post
    )

    payload = dict(WritableNestedFeatureStateSerializer(instance=feature_state).data)

    payload["enabled"] = not feature_state.enabled
    payload["feature_state_value"]["string_value"] = "new value"

    url = reverse(
        viewname="api-v1:features:featurestates-detail",
        kwargs={"pk": feature_state.id},
    )

    segment_override_updated_at = (
        segment_featurestate_and_feature_with_value.updated_at.strftime(
            get_format("DATETIME_INPUT_FORMATS")[0]
        )
    )

    expected_comment_body = (
        "Flagsmith Feature `feature_with_value` has been updated:\n"
        + "\n"
        + expected_segment_comment_body(
            project.id,
            environment.api_key,
            feature_with_value.id,
            segment_override_updated_at,
            "✅ Enabled",
            "`new value`",
        )
    )

    # When
    response = admin_client.put(path=url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK

    github_request_mock.assert_called_with(
        "https://api.github.com/repos/userexample/example-project-repo/issues/11/comments",
        json={"body": expected_comment_body},
        headers={
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )

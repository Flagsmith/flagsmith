import pytest
from pytest_structlog import StructuredLogCapture
from rest_framework import status
from rest_framework.test import APIClient

from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.github.models import GithubConfiguration
from integrations.gitlab.models import GitLabConfiguration
from projects.models import Project


@pytest.mark.django_db()
def test_create_external_resource__gitlab_issue__returns_201(
    admin_client: APIClient,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    metadata = {"title": "Fix login bug", "state": "opened"}
    organisation_id = Project.objects.get(id=project).organisation_id

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": "https://gitlab.com/testorg/testrepo/-/work_items/42",
            "feature": feature,
            "metadata": metadata,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    created = response.json()
    assert created["type"] == "GITLAB_ISSUE"
    assert created["url"] == "https://gitlab.com/testorg/testrepo/-/work_items/42"
    assert created["feature"] == feature
    assert created["metadata"] == metadata

    assert log.events == [
        {
            "level": "info",
            "event": "issue.linked",
            "organisation__id": organisation_id,
            "project__id": project,
            "feature__id": feature,
        },
    ]


@pytest.mark.django_db()
def test_create_external_resource__gitlab_merge_request__returns_201(
    admin_client: APIClient,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    metadata = {"title": "Add login button", "state": "opened"}
    organisation_id = Project.objects.get(id=project).organisation_id

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_MR",
            "url": "https://gitlab.com/testorg/testrepo/-/merge_requests/7",
            "feature": feature,
            "metadata": metadata,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["type"] == "GITLAB_MR"
    assert (
        response_json["url"] == "https://gitlab.com/testorg/testrepo/-/merge_requests/7"
    )
    assert response_json["metadata"] == metadata

    assert log.events == [
        {
            "level": "info",
            "event": "merge_request.linked",
            "organisation__id": organisation_id,
            "project__id": project,
            "feature__id": feature,
        },
    ]


@pytest.mark.django_db()
def test_create_external_resource__gitlab_issue_with_github_also_configured__returns_201(
    admin_client: APIClient,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    project_instance = Project.objects.get(id=project)
    organisation = project_instance.organisation

    GithubConfiguration.objects.create(
        organisation=organisation,
        installation_id="9999999",
    )
    GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.com",
        access_token="glpat-test-token",
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": "https://gitlab.com/testorg/testrepo/-/work_items/99",
            "feature": feature,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["type"] == "GITLAB_ISSUE"

    assert log.events == [
        {
            "level": "info",
            "event": "issue.linked",
            "organisation__id": organisation.id,
            "project__id": project,
            "feature__id": feature,
        },
    ]


@pytest.mark.django_db()
def test_list_external_resources__gitlab_issue__returns_200(
    admin_client: APIClient,
    project: int,
    feature: int,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.com/testorg/testrepo/-/work_items/42",
        type="GITLAB_ISSUE",
        feature=Feature.objects.get(id=feature),
        metadata='{"title": "Fix login bug", "state": "opened"}',
    )

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["type"] == "GITLAB_ISSUE"
    assert results[0]["metadata"] == {"title": "Fix login bug", "state": "opened"}


@pytest.mark.django_db()
def test_list_external_resources__gitlab_merge_request__returns_200(
    admin_client: APIClient,
    project: int,
    feature: int,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.com/testorg/testrepo/-/merge_requests/7",
        type="GITLAB_MR",
        feature=Feature.objects.get(id=feature),
        metadata='{"title": "Add login button", "state": "opened"}',
    )

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["type"] == "GITLAB_MR"
    assert results[0]["metadata"] == {"title": "Add login button", "state": "opened"}

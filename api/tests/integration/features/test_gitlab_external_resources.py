import pytest
from pytest_structlog import StructuredLogCapture
from rest_framework import status
from rest_framework.test import APIClient

from integrations.github.models import GithubConfiguration
from integrations.gitlab.models import GitLabConfiguration
from projects.models import Project


@pytest.mark.django_db()
def test_create_external_resource__gitlab_issue__returns_201_and_persists_metadata(
    admin_client: APIClient,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    metadata = {"title": "Fix login bug", "state": "opened", "iid": 42}
    organisation_id = Project.objects.get(id=project).organisation_id

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": "https://gitlab.com/testorg/testrepo/-/issues/42",
            "feature": feature,
            "metadata": metadata,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    created = response.json()
    assert created["type"] == "GITLAB_ISSUE"
    assert created["url"] == "https://gitlab.com/testorg/testrepo/-/issues/42"
    assert created["feature"] == feature
    assert created["metadata"] == metadata

    listed = admin_client.get(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
    ).json()["results"]
    assert len(listed) == 1
    assert listed[0]["metadata"] == metadata

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
    organisation_id = Project.objects.get(id=project).organisation_id

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_MR",
            "url": "https://gitlab.com/testorg/testrepo/-/merge_requests/7",
            "feature": feature,
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
            "url": "https://gitlab.com/testorg/testrepo/-/issues/99",
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

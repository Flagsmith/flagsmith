import freezegun
from common.projects.permissions import VIEW_PROJECT
from rest_framework.test import APIClient

from projects.code_references.models import VCSFeatureFlagCodeReferences
from projects.models import Project
from tests.types import WithProjectPermissionsCallable


@freezegun.freeze_time("2025-04-14T09:30:00-0300")
def test_CodeReferenceCreateAPIView__responds_201_with_accepted_code_references(
    project: Project,
    staff_client: APIClient,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]

    # When
    response = staff_client.post(
        f"/api/v1/projects/{project.pk}/code_references/",
        data={
            "repository_url": "https://svn.flagsmith.com/",
            "revision": "revision-hash",
            "code_references": [
                {
                    "feature_name": "feature-1",
                    "file_path": "path/to/file1.py",
                    "line_number": 10,
                },
                {
                    "feature_name": "feature-1",
                    "file_path": "path/to/file2.py",
                    "line_number": 20,
                },
                {
                    "feature_name": "feature-2",
                    "file_path": "path/to/file3.py",
                    "line_number": 30,
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 201
    assert response.data["repository_url"] == "https://svn.flagsmith.com/"
    assert response.data["revision"] == "revision-hash"
    assert len(response.data["code_references"]) == 3
    assert response.data["project"] == project.pk
    assert response.data["created_at"] == "2025-04-14T12:30:00Z"
    assert VCSFeatureFlagCodeReferences.objects.get().code_references == [
        {
            "feature_name": "feature-1",
            "file_path": "path/to/file1.py",
            "line_number": 10,
        },
        {
            "feature_name": "feature-1",
            "file_path": "path/to/file2.py",
            "line_number": 20,
        },
        {
            "feature_name": "feature-2",
            "file_path": "path/to/file3.py",
            "line_number": 30,
        },
    ]


def test_CodeReferenceCreateAPIView__responds_401_when_not_authenticated(
    project: Project,
    client: APIClient,
) -> None:
    # When
    response = client.post(
        f"/api/v1/projects/{project.pk}/code_references/",
        data={
            "repository_url": "https://svn.flagsmith.com/",
            "revision": "revision-hash",
            "code_references": [
                {
                    "feature_name": "feature-1",
                    "file_path": "path/to/file1.py",
                    "line_number": 10,
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 401
    assert not VCSFeatureFlagCodeReferences.objects.exists()


def test_CodeReferenceCreateAPIView__responds_400_when_invalid_data(
    project: Project,
    staff_client: APIClient,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])  # type: ignore[call-arg]

    # When
    response = staff_client.post(
        f"/api/v1/projects/{project.pk}/code_references/",
        data={
            "repository_url": "https://svn.flagsmith.com/",
            "revision": "revision-hash",
            "code_references": [
                {
                    "feature_name": "feature-1",
                    "file_path": "path/to/file1.py",
                    # Missing line_number
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.data == {
        "code_references": [{"line_number": ["This field is required."]}]
    }
    assert not VCSFeatureFlagCodeReferences.objects.exists()

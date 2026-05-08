import freezegun
from django.utils import timezone
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from features.models import Feature
from projects.code_references.models import ScannedCodeReferences, VCSRepository
from projects.models import Project


@freezegun.freeze_time("2025-04-14T09:30:00-0300")
def test_create_code_reference__valid_payload__returns_201_with_accepted_references(
    admin_client_new: APIClient,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given
    Feature.objects.create(project=project, name="feature-1")
    Feature.objects.create(project=project, name="feature-2")

    # When
    response = admin_client_new.post(
        f"/api/v1/projects/{project.pk}/code-references/",
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
    assert {
        scan.feature.name: scan.code_references
        for scan in ScannedCodeReferences.objects.all()
    } == {
        "feature-1": [
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
        ],
        "feature-2": [
            {
                "feature_name": "feature-2",
                "file_path": "path/to/file3.py",
                "line_number": 30,
            },
        ],
    }

    assert log.events == [
        {
            "event": "scan.created",
            "level": "info",
            "organisation__id": project.organisation_id,
            "code_references__count": 3,
            "feature__count": 2,
        },
    ]


def test_create_code_reference__not_authenticated__returns_401(
    client: APIClient,
    project: Project,
) -> None:
    # Given / When
    response = client.post(
        f"/api/v1/projects/{project.pk}/code-references/",
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
    assert not ScannedCodeReferences.objects.exists()


def test_create_code_reference__incorrect_permissions__returns_403(
    project: Project,
    staff_client: APIClient,
) -> None:
    # Given / When
    response = staff_client.post(
        f"/api/v1/projects/{project.pk}/code-references/",
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
    assert response.status_code == 403
    assert not ScannedCodeReferences.objects.exists()


def test_create_code_reference__missing_required_field__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given / When
    response = admin_client_new.post(
        f"/api/v1/projects/{project.pk}/code-references/",
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
        "code_references": [{"line_number": ["This field is required."]}],
    }
    assert not ScannedCodeReferences.objects.exists()


def test_create_code_reference__file_path_too_long__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given / When
    response = admin_client_new.post(
        f"/api/v1/projects/{project.pk}/code-references/",
        data={
            "repository_url": "https://svn.flagsmith.com/",
            "revision": "revision-hash",
            "code_references": [
                {
                    "feature_name": "feature-1",
                    "file_path": "would/you/even/" * 1000 + "file.py",
                    "line_number": 10,
                },
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.data == {
        "code_references": [
            {"file_path": ["Ensure this field has no more than 4096 characters."]}
        ],
    }
    assert not ScannedCodeReferences.objects.exists()


def test_create_code_reference__duplicate_payload__deduplicates_storage(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    Feature.objects.create(project=project, name="feature-1")
    payload = {
        "repository_url": "https://github.flagsmith.com/",
        "revision": "rev-1",
        "code_references": [
            {
                "feature_name": "feature-1",
                "file_path": "path/to/file.py",
                "line_number": 1,
            },
        ],
    }

    # When
    admin_client_new.post(
        f"/api/v1/projects/{project.pk}/code-references/", data=payload, format="json"
    )
    admin_client_new.post(
        f"/api/v1/projects/{project.pk}/code-references/", data=payload, format="json"
    )

    # Then
    assert ScannedCodeReferences.objects.count() == 1


def test_get_feature_code_references__multiple_scans_exist__returns_latest_per_repository(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
) -> None:
    # Given
    with freezegun.freeze_time("2099-01-01T10:00:00-0300"):
        backend_repository = VCSRepository.objects.create(
            project=project,
            url="https://github.flagsmith.com/backend",
            vcs_provider="github",
            last_scanned_at=timezone.now(),
        )
        ScannedCodeReferences.objects.create(
            feature=feature,
            repository=backend_repository,
            revision="backend-1",
            code_references=[
                {
                    "feature_name": feature.name,
                    "file_path": "backend/file1.py",
                    "line_number": 20,
                },
            ],
            code_references_hash="hash-backend-1",
        )
    with freezegun.freeze_time("2099-01-02T11:00:00-0300"):
        frontend_repository = VCSRepository.objects.create(
            project=project,
            url="https://github.flagsmith.com/frontend",
            vcs_provider="github",
            last_scanned_at=timezone.now(),
        )
        ScannedCodeReferences.objects.create(
            feature=feature,
            repository=frontend_repository,
            revision="frontend-2",
            code_references=[
                {
                    "feature_name": feature.name,
                    "file_path": "frontend/file1.js",
                    "line_number": 12,
                },
                {
                    "feature_name": feature.name,
                    "file_path": "frontend/file2.js",
                    "line_number": 5,
                },
            ],
            code_references_hash="hash-frontend-2",
        )

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.pk}/features/{feature.pk}/code-references/",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == [
        {
            "repository_url": "https://github.flagsmith.com/backend",
            "vcs_provider": "github",
            "revision": "backend-1",
            "last_successful_repository_scanned_at": "2099-01-01T13:00:00+00:00",
            "last_feature_found_at": "2099-01-01T13:00:00+00:00",
            "code_references": [
                {
                    "feature_name": feature.name,
                    "file_path": "backend/file1.py",
                    "line_number": 20,
                    "permalink": (
                        "https://github.flagsmith.com/backend/blob/backend-1/backend/file1.py#L20"
                    ),
                },
            ],
        },
        {
            "repository_url": "https://github.flagsmith.com/frontend",
            "vcs_provider": "github",
            "revision": "frontend-2",
            "last_successful_repository_scanned_at": "2099-01-02T14:00:00+00:00",
            "last_feature_found_at": "2099-01-02T14:00:00+00:00",
            "code_references": [
                {
                    "feature_name": feature.name,
                    "file_path": "frontend/file1.js",
                    "line_number": 12,
                    "permalink": (
                        "https://github.flagsmith.com/frontend/blob/frontend-2/frontend/file1.js#L12"
                    ),
                },
                {
                    "feature_name": feature.name,
                    "file_path": "frontend/file2.js",
                    "line_number": 5,
                    "permalink": (
                        "https://github.flagsmith.com/frontend/blob/frontend-2/frontend/file2.js#L5"
                    ),
                },
            ],
        },
    ]


def test_get_feature_code_references__feature_flag_removed__returns_no_entry(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
) -> None:
    # Given
    with freezegun.freeze_time("2099-01-01T10:00:00-0300"):
        repository = VCSRepository.objects.create(
            project=project,
            url="https://github.flagsmith.com/",
            vcs_provider="github",
            last_scanned_at=timezone.now(),
        )
        ScannedCodeReferences.objects.create(
            feature=feature,
            repository=repository,
            revision="revision-hash-1",
            code_references=[
                {
                    "feature_name": feature.name,
                    "file_path": "path/to/file1.py",
                    "line_number": 10,
                },
            ],
            code_references_hash="hash-1",
        )
    with freezegun.freeze_time("2099-01-02T11:00:00-0300"):
        repository.last_scanned_at = timezone.now()
        repository.save()

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.pk}/features/{feature.pk}/code-references/",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == []


def test_get_feature_code_references__no_scans_exist__returns_empty_list(
    admin_client_new: APIClient,
    feature: Feature,
    project: Project,
) -> None:
    # Given / When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.pk}/features/{feature.pk}/code-references/",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == []


def test_get_feature_code_references__not_authenticated__returns_401(
    client: APIClient,
    feature: Feature,
    project: Project,
) -> None:
    # Given / When
    response = client.get(
        f"/api/v1/projects/{project.pk}/features/{feature.pk}/code-references/",
    )

    # Then
    assert response.status_code == 401
    assert response.data["detail"] == "Authentication credentials were not provided."


def test_get_feature_code_references__incorrect_permissions__returns_403(
    feature: Feature,
    project: Project,
    staff_client: APIClient,
) -> None:
    # Given / When
    response = staff_client.get(
        f"/api/v1/projects/{project.pk}/features/{feature.pk}/code-references/",
    )

    # Then
    assert response.status_code == 403


def test_get_feature_code_references__feature_not_found__returns_404(
    project: Project,
    admin_client_new: APIClient,
) -> None:
    # Given / When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.pk}/features/9999/code-references/",
    )

    # Then
    assert response.status_code == 404
    assert response.data["detail"] == "No Feature matches the given query."

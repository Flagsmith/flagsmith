import freezegun
import pytest
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from rest_framework.test import APIClient

from features.models import Feature
from projects.code_references.models import FeatureFlagCodeReferencesScan
from projects.models import Project


@pytest.mark.parametrize(
    "client",
    [
        lazy_fixture("admin_master_api_key_client"),
        lazy_fixture("admin_client"),
    ],
)
@freezegun.freeze_time("2025-04-14T09:30:00-0300")
def test_CodeReferenceCreateAPIView__responds_201_with_accepted_code_references(
    client: APIClient,
    project: Project,
) -> None:
    # When
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
    assert FeatureFlagCodeReferencesScan.objects.get().code_references == [
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


@pytest.mark.parametrize(
    "client",
    [
        lazy_fixture("admin_master_api_key_client"),
        lazy_fixture("admin_client"),
    ],
)
def test_CodeReferenceCreateAPIView__responds_400_when_missing_field(
    client: APIClient,
    project: Project,
) -> None:
    # When
    response = client.post(
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
    assert not FeatureFlagCodeReferencesScan.objects.exists()


@pytest.mark.parametrize(
    "client",
    [
        lazy_fixture("admin_master_api_key_client"),
        lazy_fixture("admin_client"),
    ],
)
def test_CodeReferenceCreateAPIView__responds_400_when_file_path_too_long(
    client: APIClient,
    project: Project,
) -> None:
    # When
    response = client.post(
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
    assert not FeatureFlagCodeReferencesScan.objects.exists()


@pytest.mark.parametrize(
    "client",
    [
        lazy_fixture("admin_master_api_key_client"),
        lazy_fixture("admin_client"),
    ],
)
def test_FeatureCodeReferencesDetailAPIView__responds_200_with_code_references_for_given_feature(
    client: APIClient,
    feature: Feature,
    project: Project,
) -> None:
    # Given
    with freezegun.freeze_time("2099-01-01T10:00:00-0300"):
        FeatureFlagCodeReferencesScan.objects.create(
            project=project,
            repository_url="https://github.flagsmith.com/backend/",
            revision="backend-1",
            code_references=[
                {
                    "feature_name": feature.name,
                    "file_path": "backend/file1.py",
                    "line_number": 20,
                },
            ],
        )
        FeatureFlagCodeReferencesScan.objects.create(
            project=project,
            repository_url="https://github.flagsmith.com/frontend/",
            revision="frontend-1",
            code_references=[
                {
                    "feature_name": feature.name,
                    "file_path": "frontend/file1.js",
                    "line_number": 10,
                },
            ],
        )
    with freezegun.freeze_time("2099-01-02T11:00:00-0300"):
        FeatureFlagCodeReferencesScan.objects.create(
            project=project,
            repository_url="https://github.flagsmith.com/frontend/",
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
        )

    # When
    response = client.get(
        f"/api/v1/projects/{project.pk}/features/{feature.pk}/code-references/",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == [
        {
            "repository_url": "https://github.flagsmith.com/backend/",
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
            "repository_url": "https://github.flagsmith.com/frontend/",
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


@pytest.mark.parametrize(
    "client",
    [
        lazy_fixture("admin_master_api_key_client"),
        lazy_fixture("admin_client"),
    ],
)
def test_FeatureCodeReferencesDetailAPIView__responds_200_with_feature_flag_removed(
    client: APIClient,
    feature: Feature,
    project: Project,
) -> None:
    # Given
    with freezegun.freeze_time("2099-01-01T10:00:00-0300"):
        FeatureFlagCodeReferencesScan.objects.create(
            project=project,
            repository_url="https://github.flagsmith.com/",
            revision="revision-hash-1",
            code_references=[
                {
                    "feature_name": feature.name,
                    "file_path": "path/to/file1.py",
                    "line_number": 10,
                },
            ],
        )
    with freezegun.freeze_time("2099-01-02T11:00:00-0300"):
        FeatureFlagCodeReferencesScan.objects.create(
            project=project,
            repository_url="https://github.flagsmith.com/",
            revision="revision-hash-2",
            code_references=[],  # Feature flag removed
        )

    # When
    response = client.get(
        f"/api/v1/projects/{project.pk}/features/{feature.pk}/code-references/",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == [
        {
            "repository_url": "https://github.flagsmith.com/",
            "vcs_provider": "github",
            "revision": "revision-hash-2",
            "last_successful_repository_scanned_at": "2099-01-02T14:00:00+00:00",
            "last_feature_found_at": "2099-01-01T13:00:00+00:00",
            "code_references": [],
        },
    ]


@pytest.mark.parametrize(
    "client",
    [
        lazy_fixture("admin_master_api_key_client"),
        lazy_fixture("admin_client"),
    ],
)
def test_FeatureCodeReferencesDetailAPIView__responds_200_even_without_code_references(
    client: APIClient,
    feature: Feature,
    project: Project,
) -> None:
    # When
    response = client.get(
        f"/api/v1/projects/{project.pk}/features/{feature.pk}/code-references/",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    "client",
    [
        lazy_fixture("admin_master_api_key_client"),
        lazy_fixture("admin_client"),
    ],
)
def test_FeatureCodeReferencesDetailAPIView__responds_404_when_feature_not_found(
    project: Project,
    client: APIClient,
) -> None:
    # When
    response = client.get(
        f"/api/v1/projects/{project.pk}/features/9999/code-references/",
    )

    # Then
    assert response.status_code == 404
    assert response.data["detail"] == "No Feature matches the given query."

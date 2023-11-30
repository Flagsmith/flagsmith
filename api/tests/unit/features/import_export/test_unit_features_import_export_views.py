import json
from typing import Callable

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from features.import_export.constants import OVERWRITE_DESTRUCTIVE
from features.import_export.models import FeatureExport, FeatureImport
from projects.models import Project
from projects.permissions import VIEW_PROJECT
from projects.tags.models import Tag
from users.models import FFAdminUser


def test_list_feature_exports(
    admin_client: APIClient,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    environment2 = Environment.objects.create(
        name="Z Environment",
        project=project,
    )

    feature_export1 = FeatureExport.objects.create(
        environment=environment,
        data="[]",
    )
    feature_export2 = FeatureExport.objects.create(
        environment=environment2,
        data="[]",
    )

    url = reverse(
        "api-v1:projects:feature-exports",
        args=[project.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == 200
    assert response.data["results"][0]["environment_id"] == environment.id
    assert response.data["results"][0]["id"] == feature_export1.id
    assert response.data["results"][0]["name"].startswith(f"{environment.name} | ")

    assert response.data["results"][1]["environment_id"] == environment2.id
    assert response.data["results"][1]["id"] == feature_export2.id
    assert response.data["results"][1]["name"].startswith(f"{environment2.name} | ")


def test_list_feature_export_with_filtered_environments(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    project: Project,
    environment: Environment,
    with_project_permissions: Callable[[list[str], int], None],
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    environment2 = Environment.objects.create(
        name="Allowed admin for this environment",
        project=project,
    )
    UserEnvironmentPermission.objects.create(
        user=staff_user,
        environment=environment2,
        admin=True,
    )
    FeatureExport.objects.create(
        environment=environment,
        data="[]",
    )
    feature_export2 = FeatureExport.objects.create(
        environment=environment2,
        data="[]",
    )

    url = reverse(
        "api-v1:projects:feature-exports",
        args=[project.id],
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == 200
    assert response.data["count"] == 1

    # Only the second environment is included in the results.
    assert response.data["results"][0]["environment_id"] == environment2.id
    assert response.data["results"][0]["id"] == feature_export2.id


def test_list_feature_exports_unauthorized(
    test_user_client: APIClient,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    FeatureExport.objects.create(
        environment=environment,
        data="[]",
    )

    url = reverse(
        "api-v1:projects:feature-exports",
        args=[project.id],
    )

    # When
    response = test_user_client.get(url)

    # Then
    assert response.status_code == 403


def test_download_feature_export(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    feature_export = FeatureExport.objects.create(
        environment=environment,
        data='[{"feature": "data"}]',
    )
    url = reverse("api-v1:features:download-feature-export", args=[feature_export.id])
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == (
        f"attachment; filename=feature_export.{feature_export.id}.json"
    )
    assert response.json() == [{"feature": "data"}]


def test_download_feature_export_unauthorized(
    staff_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    feature_export = FeatureExport.objects.create(
        environment=environment,
        data='[{"feature": "data"}]',
    )
    url = reverse("api-v1:features:download-feature-export", args=[feature_export.id])
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == 403


def test_feature_import(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    assert FeatureImport.objects.count() == 0
    url = reverse(
        "api-v1:features:feature-import",
        args=[environment.id],
    )

    file_data = b"[]"
    uploaded_file = SimpleUploadedFile("test.23.json", file_data)
    data = {"file": uploaded_file, "strategy": OVERWRITE_DESTRUCTIVE}

    # When
    response = admin_client.post(url, data=data, format="multipart")

    # Then
    assert response.status_code == 201
    assert FeatureImport.objects.count() == 1
    feature_import = FeatureImport.objects.first()
    assert feature_import.strategy == OVERWRITE_DESTRUCTIVE


def test_feature_import_unauthorized(
    staff_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = (
        reverse(
            "api-v1:features:feature-import",
            args=[environment.id],
        )
        + "?strategy=overwrite-destructive"
    )
    file_data = b"[]"
    uploaded_file = SimpleUploadedFile("test.23.json", file_data)
    data = {"file": uploaded_file}

    # When
    response = staff_client.post(url, data=data, format="multipart")

    # Then
    assert response.status_code == 403


def test_create_feature_export(
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    tag = Tag.objects.create(
        label="design",
        project=environment.project,
        color="#228B22",
    )

    url = reverse("api-v1:features:create-feature-export")
    data = {"environment_id": environment.id, "tag_ids": [tag.id]}
    assert FeatureExport.objects.count() == 0

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 201
    assert response.data == {
        "environment_id": environment.id,
        "tag_ids": [tag.id],
    }
    assert FeatureExport.objects.count() == 1

    # Created by export_features_for_environment task.
    feature_export = FeatureExport.objects.all().first()
    assert feature_export.data
    assert feature_export.environment == environment


def test_create_feature_export_unauthorized(
    staff_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    tag = Tag.objects.create(
        label="design",
        project=environment.project,
        color="#228B22",
    )

    url = reverse("api-v1:features:create-feature-export")
    data = {"environment_id": environment.id, "tag_ids": [tag.id]}
    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to perform this action."
    }

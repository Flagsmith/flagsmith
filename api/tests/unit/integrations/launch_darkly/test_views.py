from unittest.mock import MagicMock

from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from integrations.launch_darkly.models import LaunchDarklyImportRequest
from projects.models import Project
from users.models import FFAdminUser


def test_launch_darkly_import_request_view__list__wrong_project__return_expected(
    import_request: LaunchDarklyImportRequest,
    project: Project,
    api_client: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:projects:imports-launch-darkly-list", args=[project.id])
    user = FFAdminUser.objects.create(email="clueless@example.com")
    api_client.force_authenticate(user)

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_launch_darkly_import_request_view__create__return_expected(
    ld_client_class_mock: MagicMock,
    project: Project,
    admin_user: FFAdminUser,
    admin_client: APIClient,
    mocker: MockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"

    process_launch_darkly_import_request_mock = mocker.patch(
        "integrations.launch_darkly.views.process_launch_darkly_import_request"
    )

    url = reverse("api-v1:projects:imports-launch-darkly-list", args=[project.id])

    # When
    response = admin_client.post(url, data={"token": token, "project_key": project_key})

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    created_import_request = LaunchDarklyImportRequest.objects.get(project=project)
    process_launch_darkly_import_request_mock.delay.assert_called_once_with(
        kwargs={"import_request_id": created_import_request.id},
    )
    assert response.json() == {
        "completed_at": None,
        "created_at": mocker.ANY,
        "created_by": admin_user.email,
        "id": created_import_request.id,
        "project": project.id,
        "status": {
            "error_messages": [],
            "requested_environment_count": 2,
            "requested_flag_count": 9,
            "result": None,
        },
        "updated_at": mocker.ANY,
    }


def test_launch_darkly_import_request_view__create__existing_unfinished__return_expected(
    ld_client_class_mock: MagicMock,
    project: Project,
    admin_client: APIClient,
    mocker: MockerFixture,
    import_request: LaunchDarklyImportRequest,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"

    process_launch_darkly_import_request_mock = mocker.patch(
        "integrations.launch_darkly.views.process_launch_darkly_import_request"
    )

    url = reverse("api-v1:projects:imports-launch-darkly-list", args=[project.id])

    # When
    response = admin_client.post(url, data={"token": token, "project_key": project_key})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == ["Existing import already in progress for this project"]
    process_launch_darkly_import_request_mock.assert_not_called()


def test_launch_darkly_import_request_view__create__existing_finished__return_expected(
    ld_client_class_mock: MagicMock,
    project: Project,
    admin_client: APIClient,
    mocker: MockerFixture,
    import_request: LaunchDarklyImportRequest,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"

    import_request.status["result"] = "success"
    import_request.save()

    process_launch_darkly_import_request_mock = mocker.patch(
        "integrations.launch_darkly.views.process_launch_darkly_import_request"
    )

    url = reverse("api-v1:projects:imports-launch-darkly-list", args=[project.id])

    # When
    response = admin_client.post(url, data={"token": token, "project_key": project_key})

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    created_import_request = LaunchDarklyImportRequest.objects.get(
        project=project,
        status__result__isnull=True,
    )
    process_launch_darkly_import_request_mock.delay.assert_called_once_with(
        kwargs={"import_request_id": created_import_request.id},
    )

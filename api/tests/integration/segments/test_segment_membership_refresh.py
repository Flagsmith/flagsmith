from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import Project


def test_update_segment__edit__enqueues_membership_refresh(
    admin_client: APIClient,
    project: int,
    segment: int,
    mocker: MockerFixture,
) -> None:
    # Given
    enqueue_membership_refresh_mock = mocker.patch(
        "segments.serializers.enqueue_membership_refresh"
    )

    # When
    response = admin_client.put(
        f"/api/v1/projects/{project}/segments/{segment}/",
        data={
            "name": "renamed",
            "project": project,
            "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    enqueue_membership_refresh_mock.assert_called_once_with(
        Project.objects.get(pk=project)
    )


def test_create_segment__new_segment__enqueues_membership_refresh(
    admin_client: APIClient,
    project: int,
    mocker: MockerFixture,
) -> None:
    # Given
    enqueue_membership_refresh_mock = mocker.patch(
        "segments.serializers.enqueue_membership_refresh"
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/segments/",
        data={
            "name": "new-segment",
            "project": project,
            "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    enqueue_membership_refresh_mock.assert_called_once_with(
        Project.objects.get(pk=project)
    )


def test_clone_segment__clone__enqueues_membership_refresh(
    admin_client: APIClient,
    project: int,
    segment: int,
    mocker: MockerFixture,
) -> None:
    # Given
    enqueue_membership_refresh_mock = mocker.patch(
        "segments.views.enqueue_membership_refresh"
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/segments/{segment}/clone/",
        data={"name": "cloned-segment"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    enqueue_membership_refresh_mock.assert_called_once_with(
        Project.objects.get(pk=project)
    )

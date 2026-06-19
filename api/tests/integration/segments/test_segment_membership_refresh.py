import json

from django.urls import reverse
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
    url = reverse(
        "api-v1:projects:project-segments-detail",
        args=[project, segment],
    )
    data = {
        "name": "renamed",
        "project": project,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
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
    url = reverse("api-v1:projects:project-segments-list", args=[project])
    data = {
        "name": "new-segment",
        "project": project,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
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
    url = reverse(
        "api-v1:projects:project-segments-clone",
        args=[project, segment],
    )
    data = {"name": "cloned-segment"}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    enqueue_membership_refresh_mock.assert_called_once_with(
        Project.objects.get(pk=project)
    )

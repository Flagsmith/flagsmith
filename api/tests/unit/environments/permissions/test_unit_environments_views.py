import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from environments.permissions.constants import VIEW_ENVIRONMENT
from environments.permissions.models import (
    EnvironmentPermissionModel,
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from organisations.models import Organisation
from tests.types import WithEnvironmentPermissionsCallable
from users.models import FFAdminUser, UserPermissionGroup


def test_user_can_list_all_user_permissions_for_an_environment(
    environment: Environment,
    admin_client: APIClient,
    staff_user: FFAdminUser,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-user-permissions-list",
        args=[environment.api_key],
    )
    with_environment_permissions([VIEW_ENVIRONMENT])

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_user_can_create_new_user_permission_for_an_environment(
    admin_client: APIClient,
    staff_user: FFAdminUser,
    organisation: Organisation,
    environment: Environment,
) -> None:
    # Given
    data = {
        "user": staff_user.id,
        "permissions": [
            "VIEW_ENVIRONMENT",
        ],
        "admin": False,
    }
    url = reverse(
        "api-v1:environments:environment-user-permissions-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["permissions"] == data["permissions"]

    user_environment_permission = UserEnvironmentPermission.objects.get(
        user=staff_user, environment=environment
    )
    assert user_environment_permission.permissions.count() == 1


def test_user_can_update_user_permission_for_a_project(
    admin_client: APIClient,
    staff_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given - empty user environment permission
    empty_permission = UserEnvironmentPermission.objects.create(
        user=staff_user, environment=environment
    )
    data = {"permissions": ["VIEW_ENVIRONMENT"]}
    url = reverse(
        "api-v1:environments:environment-user-permissions-detail",
        args=[environment.api_key, empty_permission.id],
    )

    # When
    response = admin_client.patch(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    uep = UserEnvironmentPermission.objects.get(
        user=staff_user,
        environment=environment,
    )
    assert uep.permissions.count() == 1
    assert uep.permissions.first().key == VIEW_ENVIRONMENT


def test_user_can_delete_user_permission_for_a_project(
    admin_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    uep = with_environment_permissions([VIEW_ENVIRONMENT])

    url = reverse(
        "api-v1:environments:environment-user-permissions-detail",
        args=[environment.api_key, uep.id],
    )
    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    with pytest.raises(UserEnvironmentPermission.DoesNotExist):
        uep.refresh_from_db()


def test_user_can_list_all_user_group_permissions_for_an_environment(
    admin_client: APIClient,
    environment: Environment,
    organisation: Organisation,
    staff_user: FFAdminUser,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    user_permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    user_permission_group.users.add(staff_user)

    user_group_environment_permission = (
        UserPermissionGroupEnvironmentPermission.objects.create(
            group=user_permission_group, environment=environment
        )
    )
    read_permission = EnvironmentPermissionModel.objects.get(key=VIEW_ENVIRONMENT)
    user_group_environment_permission.permissions.set([read_permission])
    url = reverse(
        "api-v1:environments:environment-user-group-permissions-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


def test_user_can_create_new_user_group_permission_for_an_environment(
    organisation: Organisation,
    staff_user: FFAdminUser,
    admin_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    new_group = UserPermissionGroup.objects.create(
        name="New group", organisation=organisation
    )
    new_group.users.add(staff_user)
    data = {
        "group": new_group.id,
        "permissions": [
            "VIEW_ENVIRONMENT",
        ],
        "admin": False,
    }
    url = reverse(
        "api-v1:environments:environment-user-group-permissions-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert sorted(response.json()["permissions"]) == sorted(data["permissions"])

    assert UserPermissionGroupEnvironmentPermission.objects.filter(
        group=new_group, environment=environment
    ).exists()
    user_group_environment_permission = (
        UserPermissionGroupEnvironmentPermission.objects.get(
            group=new_group, environment=environment
        )
    )
    assert user_group_environment_permission.permissions.count() == 1


def test_user_can_update_user_group_permission_for_an_environment(
    admin_client: APIClient,
    staff_user: FFAdminUser,
    environment: Environment,
    organisation: Organisation,
) -> None:
    # Given
    data = {"permissions": []}
    user_permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    user_permission_group.users.add(staff_user)

    user_group_environment_permission = (
        UserPermissionGroupEnvironmentPermission.objects.create(
            group=user_permission_group, environment=environment
        )
    )
    read_permission = EnvironmentPermissionModel.objects.get(key=VIEW_ENVIRONMENT)
    user_group_environment_permission.permissions.set([read_permission])

    url = reverse(
        "api-v1:environments:environment-user-group-permissions-detail",
        args=[environment.api_key, user_group_environment_permission.id],
    )

    # When
    response = admin_client.patch(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    user_group_environment_permission.refresh_from_db()
    assert user_group_environment_permission.permissions.count() == 0


def test_user_can_delete_user_permission_for_a_user_group(
    admin_client: APIClient,
    staff_user: FFAdminUser,
    environment: Environment,
    organisation: Organisation,
) -> None:
    # Given
    user_permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    user_permission_group.users.add(staff_user)

    user_group_environment_permission = (
        UserPermissionGroupEnvironmentPermission.objects.create(
            group=user_permission_group, environment=environment
        )
    )
    read_permission = EnvironmentPermissionModel.objects.get(key=VIEW_ENVIRONMENT)
    user_group_environment_permission.permissions.set([read_permission])

    url = reverse(
        "api-v1:environments:environment-user-group-permissions-detail",
        args=[environment.api_key, user_group_environment_permission.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not UserPermissionGroupEnvironmentPermission.objects.filter(
        id=user_group_environment_permission.id
    ).exists()

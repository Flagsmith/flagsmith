from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation
from organisations.permissions.models import (
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from organisations.permissions.permissions import CREATE_PROJECT
from users.models import FFAdminUser, UserPermissionGroup


def test_regular_user_cannot_create_user_organisation_permissions(
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    another_user = FFAdminUser.objects.create(email="another@testorg.com")
    another_user.add_organisation(organisation)

    url = reverse(
        "api-v1:organisations:organisation-user-permission-list",
        args=[organisation.id],
    )
    # When
    response = staff_client.post(
        url,
        data={
            "user": another_user.id,
            "permissions": [CREATE_PROJECT],
        },
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        another_user.has_organisation_permission(
            organisation=organisation, permission_key=CREATE_PROJECT
        )
        is False
    )


def test_create_user_organisation_permission(
    admin_client: APIClient,
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-user-permission-list",
        args=[organisation.id],
    )

    # When
    response = admin_client.post(
        url,
        data={"user": staff_user.id, "permissions": [CREATE_PROJECT]},
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        staff_user.has_organisation_permission(
            organisation=organisation, permission_key=CREATE_PROJECT
        )
        is True
    )


def test_list_user_organisation_permissions(
    staff_user: FFAdminUser,
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    user_permission = UserOrganisationPermission.objects.create(
        user=staff_user, organisation=organisation
    )
    user_permission.add_permission(CREATE_PROJECT)
    url = reverse(
        "api-v1:organisations:organisation-user-permission-list",
        args=[organisation.id],
    )

    url += f"?user={staff_user.id}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["user"]["email"] == staff_user.email
    assert response.data[0]["permissions"] == [CREATE_PROJECT]


def test_destroy_user_organisation_permission(
    staff_user: FFAdminUser,
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    user_permission = UserOrganisationPermission.objects.create(
        user=staff_user, organisation=organisation
    )
    user_permission.add_permission(CREATE_PROJECT)

    url = reverse(
        "api-v1:organisations:organisation-user-permission-detail",
        args=[organisation.id, user_permission.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert (
        staff_user.has_organisation_permission(
            organisation=organisation, permission_key=CREATE_PROJECT
        )
        is False
    )


def test_update_user_organisation_permission(
    staff_user: FFAdminUser,
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    user_permission = UserOrganisationPermission.objects.create(
        user=staff_user, organisation=organisation
    )
    user_permission.add_permission(CREATE_PROJECT)

    url = reverse(
        "api-v1:organisations:organisation-user-permission-detail",
        args=[organisation.id, user_permission.id],
    )

    # When
    response = admin_client.put(url, data={"user": staff_user.id, "permissions": []})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        staff_user.has_organisation_permission(
            organisation=organisation, permission_key=CREATE_PROJECT
        )
        is False
    )


def test_regular_user_cannot_create_user_group_permissions(
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    another_user = FFAdminUser.objects.create(email="another@testorg.com")
    another_user.add_organisation(organisation)
    permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    permission_group.users.add(another_user)

    url = reverse(
        "api-v1:organisations:organisation-user-group-permission-list",
        args=[organisation.id],
    )
    # When
    response = staff_client.post(
        url,
        data={
            "group": permission_group.id,
            "permissions": [CREATE_PROJECT],
        },
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        another_user.has_organisation_permission(
            organisation=organisation, permission_key=CREATE_PROJECT
        )
        is False
    )


def test_create_user_group_organisation_permission(
    staff_user: FFAdminUser,
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    permission_group.users.add(staff_user)
    url = reverse(
        "api-v1:organisations:organisation-user-group-permission-list",
        args=[organisation.id],
    )

    # When
    response = admin_client.post(
        url,
        data={"group": permission_group.id, "permissions": [CREATE_PROJECT]},
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        staff_user.has_organisation_permission(
            organisation=organisation, permission_key=CREATE_PROJECT
        )
        is True
    )


def test_list_user_group_permissions(
    admin_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    user_group_permission = UserPermissionGroupOrganisationPermission.objects.create(
        group=permission_group, organisation=organisation
    )
    user_group_permission.add_permission(CREATE_PROJECT)
    url = reverse(
        "api-v1:organisations:organisation-user-group-permission-list",
        args=[organisation.id],
    )

    url += f"?group={permission_group.id}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["group"]["name"] == permission_group.name
    assert response.data[0]["permissions"] == [CREATE_PROJECT]


def test_destroy_user_group_permission(
    admin_client: APIClient,
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    user_group_permission = UserPermissionGroupOrganisationPermission.objects.create(
        group=permission_group, organisation=organisation
    )
    user_group_permission.add_permission(CREATE_PROJECT)
    permission_group.users.add(staff_user)
    url = reverse(
        "api-v1:organisations:organisation-user-group-permission-detail",
        args=[organisation.id, user_group_permission.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert (
        staff_user.has_organisation_permission(
            organisation=organisation, permission_key=CREATE_PROJECT
        )
        is False
    )


def test_update_user_group_permission(
    admin_client: APIClient,
    staff_user: FFAdminUser,
    organisation: Organisation,
) -> None:
    # Given
    permission_group = UserPermissionGroup.objects.create(
        name="Test group", organisation=organisation
    )
    user_group_permission = UserPermissionGroupOrganisationPermission.objects.create(
        group=permission_group, organisation=organisation
    )
    user_group_permission.add_permission(CREATE_PROJECT)
    permission_group.users.add(staff_user)

    url = reverse(
        "api-v1:organisations:organisation-user-group-permission-detail",
        args=[organisation.id, user_group_permission.id],
    )

    # When
    response = admin_client.put(
        url, data={"group": permission_group.id, "permissions": []}
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        staff_user.has_organisation_permission(
            organisation=organisation, permission_key=CREATE_PROJECT
        )
        is False
    )

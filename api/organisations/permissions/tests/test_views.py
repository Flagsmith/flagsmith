from unittest import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation, OrganisationRole
from organisations.permissions.models import (
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from organisations.permissions.permissions import CREATE_PROJECT
from users.models import FFAdminUser, UserPermissionGroup


class BaseOrganisationPermissionViewSetTestCase:
    url_pattern_basename = None

    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test org")

        self.admin_user = FFAdminUser.objects.create(email="admin@testorg.com")
        self.admin_user.add_organisation(self.organisation, OrganisationRole.ADMIN)
        self.admin_user_client = APIClient()
        self.admin_user_client.force_authenticate(self.admin_user)

        self.regular_user = FFAdminUser.objects.create(email="user@testorg.com")
        self.regular_user_client = APIClient()
        self.regular_user_client.force_authenticate(self.regular_user)

        if not self.url_pattern_basename:
            raise NotImplementedError(
                "Subclasses must include url_pattern_basename attribute"
            )

        self.list_url = reverse(
            f"api-v1:organisations:{self.url_pattern_basename}-list",
            args=[self.organisation.id],
        )

    def _get_detail_url(self, obj_id: int) -> str:
        return reverse(
            f"api-v1:organisations:{self.url_pattern_basename}-detail",
            args=[self.organisation.id, obj_id],
        )


@pytest.mark.django_db
class UserOrganisationPermissionViewSetTestCase(
    BaseOrganisationPermissionViewSetTestCase, TestCase
):
    url_pattern_basename = "organisation-user-permission"

    def test_regular_user_cannot_create_user_permissions(self):
        # Given
        another_user = FFAdminUser.objects.create(email="another@testorg.com")
        another_user.add_organisation(self.organisation)

        # When
        response = self.regular_user_client.post(
            self.list_url,
            data={
                "user": another_user.id,
                "permissions": [CREATE_PROJECT],
            },
        )

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not another_user.has_organisation_permission(
            organisation=self.organisation, permission_key=CREATE_PROJECT
        )

    def test_create_user_organisation_permission(self):
        # When
        response = self.admin_user_client.post(
            self.list_url,
            data={"user": self.regular_user.id, "permissions": [CREATE_PROJECT]},
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert self.regular_user.has_organisation_permission(
            organisation=self.organisation, permission_key=CREATE_PROJECT
        )

    def test_list_user_permissions(self):
        # Given
        user_permission = UserOrganisationPermission.objects.create(
            user=self.regular_user, organisation=self.organisation
        )
        user_permission.add_permission(CREATE_PROJECT)

        url = f"{self.list_url}?user={self.regular_user.id}"

        # When
        response = self.admin_user_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert len(response_json) == 1
        assert response_json[0]["user"]["email"] == self.regular_user.email
        assert response_json[0]["permissions"] == [CREATE_PROJECT]

    def test_destroy_user_permission(self):
        # Given
        user_permission = UserOrganisationPermission.objects.create(
            user=self.regular_user, organisation=self.organisation
        )
        user_permission.add_permission(CREATE_PROJECT)

        url = self._get_detail_url(user_permission.id)

        # When
        response = self.admin_user_client.delete(url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not self.regular_user.has_organisation_permission(
            organisation=self.organisation, permission_key=CREATE_PROJECT
        )

    def test_update_user_permission(self):
        # Given
        user_permission = UserOrganisationPermission.objects.create(
            user=self.regular_user, organisation=self.organisation
        )
        user_permission.add_permission(CREATE_PROJECT)

        url = self._get_detail_url(user_permission.id)

        # When
        response = self.admin_user_client.put(
            url, data={"user": self.regular_user.id, "permissions": []}
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert not self.regular_user.has_organisation_permission(
            organisation=self.organisation, permission_key=CREATE_PROJECT
        )


@pytest.mark.django_db
class UserPermissionGroupOrganisationPermissionViewSetTestCase(
    BaseOrganisationPermissionViewSetTestCase, TestCase
):
    url_pattern_basename = "organisation-user-group-permission"

    def setUp(self) -> None:
        super(UserPermissionGroupOrganisationPermissionViewSetTestCase, self).setUp()

        self.permission_group = UserPermissionGroup.objects.create(
            name="Test group", organisation=self.organisation
        )

    def test_regular_user_cannot_create_user_group_permissions(self):
        # Given
        another_user = FFAdminUser.objects.create(email="another@testorg.com")
        another_user.add_organisation(self.organisation)
        self.permission_group.users.add(another_user)

        # When
        response = self.regular_user_client.post(
            self.list_url,
            data={
                "group": self.permission_group.id,
                "permissions": [CREATE_PROJECT],
            },
        )

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not another_user.has_organisation_permission(
            organisation=self.organisation, permission_key=CREATE_PROJECT
        )

    def test_create_user_group_organisation_permission(self):
        # Given
        self.permission_group.users.add(self.regular_user)

        # When
        response = self.admin_user_client.post(
            self.list_url,
            data={"group": self.permission_group.id, "permissions": [CREATE_PROJECT]},
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert self.regular_user.has_organisation_permission(
            organisation=self.organisation, permission_key=CREATE_PROJECT
        )

    def test_list_user_group_permissions(self):
        # Given
        user_group_permission = (
            UserPermissionGroupOrganisationPermission.objects.create(
                group=self.permission_group, organisation=self.organisation
            )
        )
        user_group_permission.add_permission(CREATE_PROJECT)

        url = f"{self.list_url}?group={self.permission_group.id}"

        # When
        response = self.admin_user_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert len(response_json) == 1
        assert response_json[0]["group"]["name"] == self.permission_group.name
        assert response_json[0]["permissions"] == [CREATE_PROJECT]

    def test_destroy_user_group_permission(self):
        # Given
        user_group_permission = (
            UserPermissionGroupOrganisationPermission.objects.create(
                group=self.permission_group, organisation=self.organisation
            )
        )
        user_group_permission.add_permission(CREATE_PROJECT)
        self.permission_group.users.add(self.regular_user)

        url = self._get_detail_url(user_group_permission.id)

        # When
        response = self.admin_user_client.delete(url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not self.regular_user.has_organisation_permission(
            organisation=self.organisation, permission_key=CREATE_PROJECT
        )

    def test_update_user_permission(self):
        # Given
        user_group_permission = (
            UserPermissionGroupOrganisationPermission.objects.create(
                group=self.permission_group, organisation=self.organisation
            )
        )
        user_group_permission.add_permission(CREATE_PROJECT)
        self.permission_group.users.add(self.regular_user)

        url = self._get_detail_url(user_group_permission.id)

        # When
        response = self.admin_user_client.put(
            url, data={"group": self.permission_group.id, "permissions": []}
        )

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert not self.regular_user.has_organisation_permission(
            organisation=self.organisation, permission_key=CREATE_PROJECT
        )

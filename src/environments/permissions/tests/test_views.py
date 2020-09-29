import json
from unittest.case import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from environments.permissions.models import (
    EnvironmentPermissionModel,
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from organisations.models import Organisation, OrganisationRole
from projects.models import Project, UserProjectPermission
from users.models import FFAdminUser, UserPermissionGroup


@pytest.mark.django_db
class UserEnvironmentPermissionsViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test")
        self.project = Project.objects.create(
            name="Test", organisation=self.organisation
        )
        self.environment = Environment.objects.create(name="Test", project=self.project)

        # Admin to bypass permission checks
        self.org_admin = FFAdminUser.objects.create(email="admin@test.com")
        self.org_admin.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # create a project user
        user = FFAdminUser.objects.create(email="user@test.com")
        user.add_organisation(self.organisation, OrganisationRole.USER)
        read_permission = EnvironmentPermissionModel.objects.get(key="VIEW_ENVIRONMENT")
        self.user_environment_permission = UserEnvironmentPermission.objects.create(
            user=user, environment=self.environment
        )
        self.user_environment_permission.permissions.set([read_permission])

        self.client = APIClient()
        self.client.force_authenticate(self.org_admin)

        self.list_url = reverse(
            "api-v1:environments:environment-user-permissions-list",
            args=[self.environment.api_key],
        )
        self.detail_url = reverse(
            "api-v1:environments:environment-user-permissions-detail",
            args=[self.environment.api_key, self.user_environment_permission.id],
        )

    def test_user_can_list_all_user_permissions_for_an_environment(self):
        # Given - set up data

        # When
        response = self.client.get(self.list_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

    def test_user_can_create_new_user_permission_for_an_environment(self):
        # Given
        new_user = FFAdminUser.objects.create(email="new_user@test.com")
        new_user.add_organisation(self.organisation, OrganisationRole.USER)
        data = {
            "user": new_user.id,
            "permissions": [
                "VIEW_ENVIRONMENT",
            ],
            "admin": False,
        }

        # When
        response = self.client.post(
            self.list_url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["permissions"] == data["permissions"]

        assert UserEnvironmentPermission.objects.filter(
            user=new_user, environment=self.environment
        ).exists()
        user_environment_permission = UserEnvironmentPermission.objects.get(
            user=new_user, environment=self.environment
        )
        assert user_environment_permission.permissions.count() == 1

    def test_user_can_update_user_permission_for_a_project(self):
        # Given - empty user environment permission
        another_user = FFAdminUser.objects.create(email="anotheruser@test.com")
        empty_permission = UserEnvironmentPermission.objects.create(
            user=another_user, environment=self.environment
        )
        data = {"permissions": ["VIEW_ENVIRONMENT"]}
        url = reverse(
            "api-v1:environments:environment-user-permissions-detail",
            args=[self.environment.api_key, empty_permission.id],
        )

        # When
        response = self.client.patch(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK

        self.user_environment_permission.refresh_from_db()
        assert (
            "VIEW_ENVIRONMENT"
            in self.user_environment_permission.permissions.values_list(
                "key", flat=True
            )
        )

    def test_user_can_delete_user_permission_for_a_project(self):
        # Given - set up data

        # When
        response = self.client.delete(self.detail_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserProjectPermission.objects.filter(
            id=self.user_environment_permission.id
        ).exists()


@pytest.mark.django_db
class UserPermissionGroupProjectPermissionsViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test")
        self.project = Project.objects.create(
            name="Test", organisation=self.organisation
        )
        self.environment = Environment.objects.create(name="Test", project=self.project)

        # Admin to bypass permission checks
        self.org_admin = FFAdminUser.objects.create(email="admin@test.com")
        self.org_admin.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # create a project user
        self.user = FFAdminUser.objects.create(email="user@test.com")
        self.user.add_organisation(self.organisation, OrganisationRole.USER)
        read_permission = EnvironmentPermissionModel.objects.get(key="VIEW_ENVIRONMENT")

        self.user_permission_group = UserPermissionGroup.objects.create(
            name="Test group", organisation=self.organisation
        )
        self.user_permission_group.users.add(self.user)

        self.user_group_environment_permission = (
            UserPermissionGroupEnvironmentPermission.objects.create(
                group=self.user_permission_group, environment=self.environment
            )
        )
        self.user_group_environment_permission.permissions.set([read_permission])

        self.client = APIClient()
        self.client.force_authenticate(self.org_admin)

        self.list_url = reverse(
            "api-v1:environments:environment-user-group-permissions-list",
            args=[self.environment.api_key],
        )
        self.detail_url = reverse(
            "api-v1:environments:environment-user-group-permissions-detail",
            args=[self.environment.api_key, self.user_group_environment_permission.id],
        )

    def test_user_can_list_all_user_group_permissions_for_an_environment(self):
        # Given - set up data

        # When
        response = self.client.get(self.list_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

    def test_user_can_create_new_user_group_permission_for_an_environment(self):
        # Given
        new_group = UserPermissionGroup.objects.create(
            name="New group", organisation=self.organisation
        )
        new_group.users.add(self.user)
        data = {
            "group": new_group.id,
            "permissions": [
                "VIEW_ENVIRONMENT",
            ],
            "admin": False,
        }

        # When
        response = self.client.post(
            self.list_url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert sorted(response.json()["permissions"]) == sorted(data["permissions"])

        assert UserPermissionGroupEnvironmentPermission.objects.filter(
            group=new_group, environment=self.environment
        ).exists()
        user_group_environment_permission = (
            UserPermissionGroupEnvironmentPermission.objects.get(
                group=new_group, environment=self.environment
            )
        )
        assert user_group_environment_permission.permissions.count() == 1

    def test_user_can_update_user_group_permission_for_an_environment(self):
        # Given
        data = {"permissions": []}

        # When
        response = self.client.patch(
            self.detail_url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK

        self.user_group_environment_permission.refresh_from_db()
        assert self.user_group_environment_permission.permissions.count() == 0

    def test_user_can_delete_user_permission_for_a_project(self):
        # Given - set up data

        # When
        response = self.client.delete(self.detail_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserPermissionGroupEnvironmentPermission.objects.filter(
            id=self.user_group_environment_permission.id
        ).exists()

import json
from unittest import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation, OrganisationRole
from organisations.permissions.models import (
    OrganisationPermissionModel,
    UserOrganisationPermission,
)
from organisations.permissions.permissions import CREATE_PROJECT
from projects.models import (
    Project,
    ProjectPermissionModel,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from users.models import FFAdminUser, UserPermissionGroup


@pytest.mark.django_db
class ProjectTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = FFAdminUser.objects.create(email="admin@test.com")
        self.client.force_authenticate(user=self.user)

        self.organisation = Organisation.objects.create(name="Test org")
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        self.list_url = reverse("api-v1:projects:project-list")

        self.create_project_permission = OrganisationPermissionModel.objects.get(
            key=CREATE_PROJECT
        )

    def _get_detail_url(self, project_id):
        return reverse("api-v1:projects:project-detail", args=[project_id])

    def test_project_response_have_is_migration_done(self):
        project_name = "project1"
        data = {"name": project_name, "organisation": self.organisation.id}

        # When
        response = self.client.post(self.list_url, data=data)
        # Then
        assert response.json()["is_identity_migration_done"] is False

    def test_should_create_a_project(self):
        # Given
        project_name = "project1"
        data = {"name": project_name, "organisation": self.organisation.id}

        # When
        response = self.client.post(self.list_url, data=data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert Project.objects.filter(name=project_name).count() == 1

        # and user is admin
        assert UserProjectPermission.objects.filter(
            user=self.user, project__id=response.json()["id"], admin=True
        )

        # and they can get the project
        url = reverse("api-v1:projects:project-detail", args=[response.json()["id"]])
        get_project_response = self.client.get(url)
        assert get_project_response.status_code == status.HTTP_200_OK

    def test_create_project_returns_403_if_user_is_not_organisation_admin(self):
        # Given
        not_permitted_user = FFAdminUser.objects.create(email="notpermitted@org.com")
        not_permitted_user.add_organisation(self.organisation)
        not_permitted_user.save()
        client = APIClient()
        client.force_authenticate(not_permitted_user)

        project_name = "project1"
        data = {"name": project_name, "organisation": self.organisation.id}

        # When
        response = client.post(self.list_url, data=data)

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert (
            response.json()["detail"]
            == "You do not have permission to perform this action."
        )

    def test_user_with_create_project_permission_can_create_project(self):
        # Given
        permitted_user = FFAdminUser.objects.create(email="permitted@org.com")
        permitted_user.add_organisation(self.organisation)
        permitted_user.save()
        user_permission = UserOrganisationPermission.objects.create(
            organisation=self.organisation, user=permitted_user
        )
        user_permission.permissions.add(self.create_project_permission)
        user_permission.save()
        client = APIClient()
        client.force_authenticate(permitted_user)

        # When
        response = client.post(
            self.list_url,
            data={"name": "some proj", "organisation": self.organisation.id},
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED

    def test_user_with_create_project_permission_cannot_create_project_if_restricted_to_admin(
        self,
    ):
        # Given
        new_organisation = Organisation.objects.create(
            name="New org", restrict_project_create_to_admin=True
        )
        permitted_user = FFAdminUser.objects.create(email="permitted@org.com")
        user_permission = UserOrganisationPermission.objects.create(
            organisation=new_organisation, user=permitted_user
        )
        user_permission.permissions.add(self.create_project_permission)
        user_permission.save()

        # When
        response = self.client.post(
            self.list_url,
            data={"name": "some proj", "organisation": new_organisation.id},
        )

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_user_can_list_project_permission(self):
        # Given
        url = reverse("api-v1:projects:project-permissions")

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert (
            len(response.json()) == 4
        )  # hard code how many permissions we expect there to be

    def test_user_with_view_project_permission_can_view_project(self):
        # Given
        user = FFAdminUser.objects.create(email="test@test.com")
        project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        user_project_permission = UserProjectPermission.objects.create(
            user=user, project=project
        )
        user_project_permission.add_permission("VIEW_PROJECT")
        url = reverse("api-v1:projects:project-detail", args=[project.id])

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

    def test_user_with_view_project_permission_can_get_their_permissions_for_a_project(
        self,
    ):
        # Given
        user = FFAdminUser.objects.create(email="test@test.com")
        project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )
        user.add_organisation(self.organisation)
        user_project_permission = UserProjectPermission.objects.create(
            user=user, project=project
        )
        user_project_permission.add_permission("VIEW_PROJECT")
        url = reverse("api-v1:projects:project-my-permissions", args=[project.id])

        # When
        self.client.force_authenticate(user)
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class UserProjectPermissionsViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test")
        self.project = Project.objects.create(
            name="Test", organisation=self.organisation
        )

        # Admin to bypass permission checks
        self.org_admin = FFAdminUser.objects.create(email="admin@test.com")
        self.org_admin.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # create a project user
        user = FFAdminUser.objects.create(email="user@test.com")
        user.add_organisation(self.organisation, OrganisationRole.USER)
        read_permission = ProjectPermissionModel.objects.get(key="VIEW_PROJECT")
        self.user_project_permission = UserProjectPermission.objects.create(
            user=user, project=self.project
        )
        self.user_project_permission.permissions.set([read_permission])

        self.client = APIClient()
        self.client.force_authenticate(self.org_admin)

        self.list_url = reverse(
            "api-v1:projects:project-user-permissions-list", args=[self.project.id]
        )
        self.detail_url = reverse(
            "api-v1:projects:project-user-permissions-detail",
            args=[self.project.id, self.user_project_permission.id],
        )

    def test_user_can_list_all_user_permissions_for_a_project(self):
        # Given - set up data

        # When
        response = self.client.get(self.list_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

    def test_user_can_create_new_user_permission_for_a_project(self):
        # Given
        new_user = FFAdminUser.objects.create(email="new_user@test.com")
        new_user.add_organisation(self.organisation, OrganisationRole.USER)
        data = {
            "user": new_user.id,
            "permissions": ["VIEW_PROJECT", "CREATE_ENVIRONMENT"],
            "admin": False,
        }

        # When
        response = self.client.post(
            self.list_url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert sorted(response.json()["permissions"]) == sorted(data["permissions"])

        assert UserProjectPermission.objects.filter(
            user=new_user, project=self.project
        ).exists()
        user_project_permission = UserProjectPermission.objects.get(
            user=new_user, project=self.project
        )
        assert user_project_permission.permissions.count() == 2

    def test_user_can_update_user_permission_for_a_project(self):
        # Given
        data = {"permissions": ["CREATE_FEATURE"]}

        # When
        response = self.client.patch(
            self.detail_url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK

        self.user_project_permission.refresh_from_db()
        assert "CREATE_FEATURE" in self.user_project_permission.permissions.values_list(
            "key", flat=True
        )

    def test_user_can_delete_user_permission_for_a_project(self):
        # Given - set up data

        # When
        response = self.client.delete(self.detail_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserProjectPermission.objects.filter(
            id=self.user_project_permission.id
        ).exists()


@pytest.mark.django_db
class UserPermissionGroupProjectPermissionsViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test")
        self.project = Project.objects.create(
            name="Test", organisation=self.organisation
        )

        # Admin to bypass permission checks
        self.org_admin = FFAdminUser.objects.create(email="admin@test.com")
        self.org_admin.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # create a project user
        self.user = FFAdminUser.objects.create(email="user@test.com")
        self.user.add_organisation(self.organisation, OrganisationRole.USER)
        read_permission = ProjectPermissionModel.objects.get(key="VIEW_PROJECT")

        self.user_permission_group = UserPermissionGroup.objects.create(
            name="Test group", organisation=self.organisation
        )
        self.user_permission_group.users.add(self.user)

        self.user_group_project_permission = (
            UserPermissionGroupProjectPermission.objects.create(
                group=self.user_permission_group, project=self.project
            )
        )
        self.user_group_project_permission.permissions.set([read_permission])

        self.client = APIClient()
        self.client.force_authenticate(self.org_admin)

        self.list_url = reverse(
            "api-v1:projects:project-user-group-permissions-list",
            args=[self.project.id],
        )
        self.detail_url = reverse(
            "api-v1:projects:project-user-group-permissions-detail",
            args=[self.project.id, self.user_group_project_permission.id],
        )

    def test_user_can_list_all_user_group_permissions_for_a_project(self):
        # Given - set up data

        # When
        response = self.client.get(self.list_url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 1

    def test_user_can_create_new_user_group_permission_for_a_project(self):
        # Given
        new_group = UserPermissionGroup.objects.create(
            name="New group", organisation=self.organisation
        )
        new_group.users.add(self.user)
        data = {
            "group": new_group.id,
            "permissions": ["VIEW_PROJECT", "CREATE_ENVIRONMENT"],
            "admin": False,
        }

        # When
        response = self.client.post(
            self.list_url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert sorted(response.json()["permissions"]) == sorted(data["permissions"])

        assert UserPermissionGroupProjectPermission.objects.filter(
            group=new_group, project=self.project
        ).exists()
        user_group_project_permission = (
            UserPermissionGroupProjectPermission.objects.get(
                group=new_group, project=self.project
            )
        )
        assert user_group_project_permission.permissions.count() == 2

    def test_user_can_update_user_group_permission_for_a_project(self):
        # Given
        data = {"permissions": ["CREATE_FEATURE"]}

        # When
        response = self.client.patch(
            self.detail_url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_200_OK

        self.user_group_project_permission.refresh_from_db()
        assert (
            "CREATE_FEATURE"
            in self.user_group_project_permission.permissions.values_list(
                "key", flat=True
            )
        )

    def test_user_can_delete_user_permission_for_a_project(self):
        # Given - set up data

        # When
        response = self.client.delete(self.detail_url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not UserPermissionGroupProjectPermission.objects.filter(
            id=self.user_group_project_permission.id
        ).exists()

from unittest import TestCase, mock

import pytest

from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from environments.permissions.permissions import (
    EnvironmentAdminPermission,
    EnvironmentPermissions,
    NestedEnvironmentPermissions,
)
from organisations.models import Organisation, OrganisationRole
from projects.models import (
    Project,
    ProjectPermissionModel,
    UserProjectPermission,
)
from users.models import FFAdminUser

mock_view = mock.MagicMock()
mock_request = mock.MagicMock()

environment_permissions = EnvironmentPermissions()
nested_environment_permissions = NestedEnvironmentPermissions()
environment_admin_permissions = EnvironmentAdminPermission()


def test_environment_admin_permissions_has_permissions_returns_false_for_non_admin_user(
    environment, django_user_model, mocker
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    mocked_request = mocker.MagicMock()
    mocked_request.user = user

    mocked_view = mocker.MagicMock()
    mocked_view.kwargs = {"environment_api_key": environment.api_key}

    # When
    has_permission = environment_admin_permissions.has_permission(
        mocked_request, mocked_view
    )
    assert has_permission is False


def test_environment_admin_permissions_has_permissions_returns_true_for_admin_user(
    environment, django_user_model, mocker
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    UserEnvironmentPermission.objects.create(
        user=user, environment=environment, admin=True
    )
    mocked_request = mocker.MagicMock()
    mocked_request.user = user

    mocked_view = mocker.MagicMock()
    mocked_view.kwargs = {"environment_api_key": environment.api_key}

    # When
    has_permission = environment_admin_permissions.has_permission(
        mocked_request, mocked_view
    )
    assert has_permission is True


@pytest.mark.django_db
class EnvironmentPermissionsTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test")

        self.org_admin = FFAdminUser.objects.create(email="admin@test.com")
        self.org_admin.add_organisation(self.organisation, OrganisationRole.ADMIN)

        self.user = FFAdminUser.objects.create(email="user@test.com")
        self.user.add_organisation(self.organisation, OrganisationRole.USER)

        self.project = Project.objects.create(
            name="Test Project", organisation=self.organisation
        )

        self.environment = Environment.objects.create(
            name="Test Environment", project=self.project
        )

    def test_org_admin_can_create_environment_for_any_project(self):
        # Given
        mock_view.action = "create"
        mock_view.detail = False
        mock_request.user = self.org_admin
        mock_request.data = {"project": self.project.id, "name": "Test environment"}

        # When
        result = environment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

    def test_project_admin_can_create_environment_in_project(self):
        # Given
        UserProjectPermission.objects.create(
            user=self.user, project=self.project, admin=True
        )
        mock_request.user = self.user
        mock_view.action = "create"
        mock_view.detail = False
        mock_request.data = {"project": self.project.id, "name": "Test environment"}

        # When
        result = environment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

    def test_project_user_with_create_environment_permission_can_create_environment(
        self,
    ):
        # Given
        create_environment_permission = ProjectPermissionModel.objects.get(
            key="CREATE_ENVIRONMENT"
        )
        user_project_permission = UserProjectPermission.objects.create(
            user=self.user, project=self.project
        )
        user_project_permission.permissions.set([create_environment_permission])
        mock_request.user = self.user
        mock_view.action = "create"
        mock_view.detail = False
        mock_request.data = {"project": self.project.id, "name": "Test environment"}

        # When
        result = environment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

    def test_project_user_without_create_environment_permission_cannot_create_environment(
        self,
    ):
        # Given
        mock_request.user = self.user
        mock_view.action = "create"
        mock_view.detail = False
        mock_request.data = {"project": self.project.id, "name": "Test environment"}

        # When
        result = environment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert not result

    def test_all_users_can_list_environments_for_project(self):
        # Given
        mock_view.action = "list"
        mock_view.detail = False
        mock_request.user = self.user

        # When
        result = environment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

    def test_organisation_admin_can_delete_environment(self):
        # Given
        mock_view.action = "delete"
        mock_view.detail = True
        mock_request.user = self.org_admin

        # When
        result = environment_permissions.has_object_permission(
            mock_request, mock_view, self.environment
        )

        # Then
        assert result

    def test_project_admin_can_delete_environment(self):
        # Given
        UserProjectPermission.objects.create(
            user=self.user, project=self.project, admin=True
        )
        mock_request.user = self.user
        mock_view.action = "delete"
        mock_view.detail = True

        # When
        result = environment_permissions.has_object_permission(
            mock_request, mock_view, self.environment
        )

        # Then
        assert result

    def test_environment_admin_can_delete_environment(self):
        # Given
        UserEnvironmentPermission.objects.create(
            user=self.user, environment=self.environment, admin=True
        )
        mock_request.user = self.user
        mock_view.action = "delete"
        mock_view.detail = True

        # When
        result = environment_permissions.has_object_permission(
            mock_request, mock_view, self.environment
        )

        # Then
        assert result

    def test_regular_user_cannot_delete_environment(self):
        # Given
        mock_request.user = self.user
        mock_view.action = "delete"
        mock_view.detail = True

        # When
        result = environment_permissions.has_object_permission(
            mock_request, mock_view, self.environment
        )

        # Then
        assert not result


@pytest.mark.django_db
class NestedEnvironmentPermissionsTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test")

        self.org_admin = FFAdminUser.objects.create(email="admin@test.com")
        self.org_admin.add_organisation(self.organisation, OrganisationRole.ADMIN)

        self.user = FFAdminUser.objects.create(email="user@test.com")
        self.user.add_organisation(self.organisation, OrganisationRole.USER)

        self.project = Project.objects.create(
            name="Test Project", organisation=self.organisation
        )

        self.environment = Environment.objects.create(
            name="Test Environment", project=self.project
        )

        self.identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )

    def test_organisation_admin_has_create_permission(self):
        # Given
        mock_view.action = "create"
        mock_view.detail = False
        mock_request.user = self.org_admin
        mock_view.kwargs = {"environment_api_key": self.environment.api_key}

        # When
        result = nested_environment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

    def test_environment_admin_has_create_permission(self):
        # Given
        UserEnvironmentPermission.objects.create(
            user=self.user, environment=self.environment, admin=True
        )
        mock_view.action = "create"
        mock_view.detail = False
        mock_view.kwargs = {"environment_api_key": self.environment.api_key}
        mock_request.user = self.user

        # When
        result = nested_environment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

    def test_regular_user_does_not_have_create_permission(self):
        # Given
        mock_view.action = "create"
        mock_view.detail = False
        mock_request.user = self.user
        mock_view.kwargs = {"environment_api_key": self.environment.api_key}

        # When
        result = nested_environment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert not result

    def test_organisation_admin_has_destroy_permission(self):
        # Given
        mock_view.action = "destroy"
        mock_view.detail = True
        mock_request.user = self.org_admin

        # When
        result = nested_environment_permissions.has_object_permission(
            mock_request, mock_view, self.identity
        )

        # Then
        assert result

    def test_environment_admin_has_destroy_permission(self):
        # Given
        UserEnvironmentPermission.objects.create(
            user=self.user, environment=self.environment, admin=True
        )
        mock_view.action = "destroy"
        mock_view.detail = True
        mock_request.user = self.user

        # When
        result = nested_environment_permissions.has_object_permission(
            mock_request, mock_view, self.identity
        )

        # Then
        assert result

    def test_regular_user_does_not_have_destroy_permission(self):
        # Given
        mock_view.action = "destroy"
        mock_view.detail = True
        mock_request.user = self.user

        # When
        result = nested_environment_permissions.has_object_permission(
            mock_request, mock_view, self.identity
        )

        # Then
        assert not result

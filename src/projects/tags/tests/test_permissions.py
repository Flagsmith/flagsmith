from unittest import TestCase, mock

import pytest

from organisations.models import Organisation
from projects.models import Project, UserProjectPermission
from projects.tags.models import Tag
from projects.tags.permissions import TagPermissions
from users.models import FFAdminUser

mock_request = mock.MagicMock()
mock_view = mock.MagicMock()

permissions = TagPermissions()


@pytest.mark.django_db
class TagPermissionsTestCase(TestCase):
    def setUp(self):
        organisation = Organisation.objects.create(name="Test org")
        self.project = Project.objects.create(name="Test project", organisation=organisation)
        self.tag = Tag.objects.create(label="test", project=self.project)
        mock_view.kwargs = {'project_pk': self.project.id}

        self.project_admin = FFAdminUser.objects.create(email="project_admin@example.com")
        self.project_admin.add_organisation(organisation)
        UserProjectPermission.objects.create(user=self.project_admin, admin=True, project=self.project)

        self.project_user = FFAdminUser.objects.create(email="project_user@example.com")
        self.project_user.add_organisation(organisation)
        user_project_permission = UserProjectPermission.objects.create(user=self.project_user, project=self.project)
        user_project_permission.add_permission('VIEW_PROJECT')

    def test_project_admin_has_permission(self):
        # Given
        mock_request.user = self.project_admin

        # When
        results = []
        for action in ['list', 'create']:
            mock_view.action = action
            results.append(permissions.has_permission(mock_request, mock_view))

        # Then
        assert all(results)

    def test_project_admin_has_object_permission(self):
        # Given
        mock_request.user = self.project_admin

        # When
        results = []
        for action in ['update', 'delete', 'detail']:
            mock_view.action = action
            results.append(permissions.has_object_permission(mock_request, mock_view, self.tag))

        # Then
        assert all(results)

    def test_project_user_has_list_permission(self):
        # Given
        mock_request.user = self.project_user
        mock_view.detail = False

        # When
        mock_view.action = 'list'
        result = permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

    def test_project_user_has_no_create_permission(self):
        # Given
        mock_request.user = self.project_user
        mock_view.detail = False

        # When
        mock_view.action = 'create'
        result = permissions.has_permission(mock_request, mock_view)

        # Then
        assert not result

    def test_project_user_has_no_update_or_delete_permission(self):
        # Given
        mock_request.user = self.project_user

        # When
        results = []
        for action in ['update', 'delete']:
            mock_view.action = action
            results.append(permissions.has_object_permission(mock_request, mock_view, self.tag))

        # Then
        assert all(result is False for result in results)

    def test_project_user_has_detail_permission(self):
        # Given
        mock_request.user = self.project_user

        # When
        mock_view.action = 'detail'
        result = permissions.has_object_permission(mock_request, mock_view, self.tag)

        # Then
        assert result

from unittest import TestCase, mock

import pytest

from environments.models import Environment, UserEnvironmentPermission, Identity
from organisations.models import Organisation
from projects.models import Project, UserProjectPermission
from segments.models import Segment
from segments.permissions import SegmentPermissions
from users.models import FFAdminUser


mock_request = mock.MagicMock()
mock_view = mock.MagicMock()

segment_permissions = SegmentPermissions()


@pytest.mark.django_db
class SegmentPermissionsTestCase(TestCase):
    def setUp(self) -> None:
        organisation = Organisation.objects.create(name='Test org')
        self.project = Project.objects.create(name='Test project', organisation=organisation)
        self.segment = Segment.objects.create(name='Test segment', project=self.project)

        self.project_admin = FFAdminUser.objects.create(email='project_admin@test.com')
        mock_view.kwargs = {'project_pk': self.project.id}

        mock_request.query_params = {}

        UserProjectPermission.objects.create(user=self.project_admin, admin=True, project=self.project)

        self.project_user = FFAdminUser.objects.create(email='user@test.com')

        user_project_permissions = UserProjectPermission.objects.create(project=self.project, user=self.project_user)
        user_project_permissions.add_permission('VIEW_PROJECT')

    def test_project_admin_has_permission(self):
        # Given
        mock_request.user = self.project_admin

        # When
        results = []
        for action in ('list', 'create'):
            mock_view.action = action
            results.append(segment_permissions.has_permission(mock_request, mock_view))

        # then
        assert all(results)

    def test_project_admin_has_object_permission(self):
        # Given
        UserProjectPermission.objects.create(user=self.project_admin, project=self.project, admin=True)
        mock_request.user = self.project_admin

        # When
        results = []
        for action in ('update', 'destroy', 'retrieve'):
            mock_view.action = action
            results.append(segment_permissions.has_object_permission(mock_request, mock_view, self.segment))

        # then
        assert all(results)

    def test_project_user_has_list_permission(self):
        # Given
        mock_request.user = self.project_user
        mock_view.detail = False

        # When
        mock_view.action = 'list'
        result = segment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

    def test_project_user_has_no_create_permission(self):
        # Given
        mock_request.user = self.project_user
        mock_view.detail = False

        # When
        mock_view.action = 'create'
        result = segment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert not result

    def test_project_user_has_no_object_permission(self):
        # Given
        mock_request.user = self.project_user

        # When
        results = []
        for action in ('retrieve', 'destroy', 'update'):
            mock_view.action = action
            results.append(segment_permissions.has_object_permission(mock_request, mock_view, self.segment))

        # Then
        assert all(not result for result in results)

    def test_environment_admin_can_get_segments_for_an_identity(self):
        # Given
        environment = Environment.objects.create(name='Test environment', project=self.project)
        identity = Identity.objects.create(identifier='test', environment=environment)
        user = FFAdminUser.objects.create(email='environment_admin@test.com')
        UserEnvironmentPermission.objects.create(user=user, admin=True, environment=environment)
        mock_request.query_params['identity'] = identity.id

        # When
        result = segment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

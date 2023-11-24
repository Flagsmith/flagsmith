import uuid
from unittest import TestCase, mock

import pytest

from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from organisations.models import Organisation
from permissions.models import PermissionModel
from projects.models import Project, UserProjectPermission
from projects.permissions import VIEW_PROJECT
from segments.models import Segment
from segments.permissions import SegmentPermissions
from users.models import FFAdminUser

mock_request = mock.MagicMock()
mock_view = mock.MagicMock()

segment_permissions = SegmentPermissions()


@pytest.mark.django_db
class SegmentPermissionsTestCase(TestCase):
    def setUp(self) -> None:
        organisation = Organisation.objects.create(name="Test org")
        self.project = Project.objects.create(
            name="Test project", organisation=organisation
        )
        self.segment = Segment.objects.create(name="Test segment", project=self.project)

        self.project_admin = FFAdminUser.objects.create(email="project_admin@test.com")
        mock_view.kwargs = {"project_pk": self.project.id}

        mock_request.query_params = {}

        self.project_user = FFAdminUser.objects.create(email="user@test.com")

        user_project_permissions = UserProjectPermission.objects.create(
            project=self.project, user=self.project_user
        )
        user_project_permissions.add_permission(VIEW_PROJECT)

    def test_project_admin_has_permission(self):
        # Given
        mock_request.user = self.project_admin

        # When
        results = []
        for action in ("list", "create"):
            mock_view.action = action
            results.append(segment_permissions.has_permission(mock_request, mock_view))

        # then
        assert all(results)

    def test_project_admin_has_object_permission(self):
        # Given
        UserProjectPermission.objects.create(
            user=self.project_admin, project=self.project, admin=True
        )
        mock_request.user = self.project_admin

        # When
        results = []
        for action in ("update", "destroy", "retrieve"):
            mock_view.action = action
            results.append(
                segment_permissions.has_object_permission(
                    mock_request, mock_view, self.segment
                )
            )

        # then
        assert all(results)

    def test_project_user_has_list_permission(self):
        # Given
        mock_request.user = self.project_user
        mock_view.detail = False

        # When
        mock_view.action = "list"
        result = segment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert result

    def test_project_user_has_no_create_permission(self):
        # Given
        mock_request.user = self.project_user
        mock_view.detail = False

        # When
        mock_view.action = "create"
        result = segment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert not result

    def test_project_user_has_object_permission(self):
        # Given
        mock_request.user = self.project_user

        # When
        for action, expected_result in (
            ("retrieve", True),
            ("destroy", False),
            ("update", False),
            ("partial_update", False),
        ):
            mock_view.action = action
            # Then
            assert (
                segment_permissions.has_object_permission(
                    mock_request, mock_view, self.segment
                )
                == expected_result
            )

    def test_environment_admin_can_get_segments_for_an_identity(self):
        # Given
        environment = Environment.objects.create(
            name="Test environment", project=self.project
        )
        identity = Identity.objects.create(identifier="test", environment=environment)
        user = FFAdminUser.objects.create(email="environment_admin@test.com")
        UserEnvironmentPermission.objects.create(
            user=user, admin=True, environment=environment
        )
        mock_request.query_params["identity"] = identity.id

        # When
        result = segment_permissions.has_permission(mock_request, mock_view)

        # Then
        assert result


def test_user_with_view_project_permission_can_list_segments_for_an_identity(
    segment, django_user_model, mocker
):
    # Given
    permissions = SegmentPermissions()
    identity_uuid = uuid.uuid4()

    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(segment.project.organisation)

    user_project_permission = UserProjectPermission.objects.create(
        user=user, project=segment.project
    )
    user_project_permission.permissions.add(
        PermissionModel.objects.get(key=VIEW_PROJECT)
    )

    request = mocker.MagicMock(user=user, query_params={"identity": identity_uuid})
    view = mocker.MagicMock(action="list", kwargs={"project_pk": segment.project_id})

    # When
    result = permissions.has_permission(request, view)

    # Then
    assert result

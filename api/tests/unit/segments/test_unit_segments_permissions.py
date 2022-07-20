import uuid

from permissions.models import PermissionModel
from projects.models import UserProjectPermission
from segments.permissions import SegmentPermissions


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
        PermissionModel.objects.get(key="VIEW_PROJECT")
    )

    request = mocker.MagicMock(user=user, query_params={"identity": identity_uuid})
    view = mocker.MagicMock(action="list", kwargs={"project_pk": segment.project_id})

    # When
    result = permissions.has_permission(request, view)

    # Then
    assert result

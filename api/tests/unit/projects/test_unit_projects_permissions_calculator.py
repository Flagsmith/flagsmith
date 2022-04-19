import pytest

from organisations.models import OrganisationRole
from projects.models import (
    ProjectPermissionModel,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from projects.permissions_calculator import ProjectPermissionsCalculator
from users.models import UserPermissionGroup


@pytest.mark.parametrize(
    "user_permissions, user_admin, group_permissions, group_admin, expected_permissions, expected_admin",
    (
        (set(), False, set(), False, set(), False),
        ({"VIEW_PROJECT"}, False, set(), False, {"VIEW_PROJECT"}, False),
        (set(), False, {"VIEW_PROJECT"}, False, {"VIEW_PROJECT"}, False),
        (set(), True, set(), False, set(), True),
        (set(), False, set(), True, set(), True),
        (
            {"VIEW_PROJECT", "CREATE_ENVIRONMENT"},
            False,
            set(),
            False,
            {"VIEW_PROJECT", "CREATE_ENVIRONMENT"},
            False,
        ),
        (
            {"CREATE_ENVIRONMENT"},
            False,
            {"VIEW_PROJECT"},
            False,
            {"VIEW_PROJECT", "CREATE_ENVIRONMENT"},
            False,
        ),
        (set(), True, set(), True, set(), True),
    ),
)
def test_permissions_calculator_get_user_project_permission_data(
    project,
    django_user_model,
    user_permissions,
    user_admin,
    group_permissions,
    group_admin,
    expected_permissions,
    expected_admin,
):
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(project.organisation, OrganisationRole.USER)

    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=project.organisation
    )
    group.users.add(user)

    user_project_permission = UserProjectPermission.objects.create(
        user=user, project=project, admin=user_admin
    )
    group_project_permission = UserPermissionGroupProjectPermission.objects.create(
        group=group, project=project, admin=group_admin
    )

    project_permissions = {pm.key: pm for pm in ProjectPermissionModel.objects.all()}

    for permission_key in user_permissions:
        user_project_permission.permissions.add(project_permissions[permission_key])

    for permission_key in group_permissions:
        group_project_permission.permissions.add(project_permissions[permission_key])

    permission_calculator = ProjectPermissionsCalculator(project_id=project.id)

    # When
    user_permission_data = permission_calculator.get_user_project_permission_data(
        user_id=user.id
    )

    # Then
    assert user_permission_data.admin == expected_admin
    assert user_permission_data.permissions == expected_permissions

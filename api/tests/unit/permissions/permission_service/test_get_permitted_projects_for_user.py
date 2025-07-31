import pytest
from common.projects.permissions import (
    CREATE_ENVIRONMENT,
    DELETE_FEATURE,
    VIEW_PROJECT,
)
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]

from organisations.models import Organisation, UserOrganisation
from permissions.models import PermissionModel
from permissions.permission_service import get_permitted_projects_for_user
from projects.models import (
    Project,
    ProjectPermissionModel,
    UserPermissionGroupProjectPermission,
)
from users.models import FFAdminUser, UserPermissionGroup


def test_get_permitted_projects_for_user_returns_all_projects_for_org_admin(  # type: ignore[no-untyped-def]
    admin_user, project, project_two
):
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert get_permitted_projects_for_user(admin_user, permission).count() == 2


@pytest.mark.parametrize(
    "project_admin",
    [
        (lazy_fixture("project_admin_via_user_permission")),
        (lazy_fixture("project_admin_via_user_permission_group")),
    ],
)
def test_get_permitted_projects_for_user_returns_the_project_for_project_admin(  # type: ignore[no-untyped-def]
    test_user, project, project_admin, project_two
):
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert get_permitted_projects_for_user(test_user, permission).count() == 1


def test_get_permitted_projects_for_user_returns_correct_project(  # type: ignore[no-untyped-def]
    test_user,
    project,
    project_permission_using_user_permission,
    project_permission_using_user_permission_group,
):
    # First, let's assert that the user does not have access to any project
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        assert get_permitted_projects_for_user(test_user, permission).count() == 0

    # Next, let's give user some permissions using `user_permission`
    project_permission_using_user_permission.permissions.add(VIEW_PROJECT)
    project_permission_using_user_permission.permissions.add(CREATE_ENVIRONMENT)

    # Next, let's assert that the project is returned only for those permissions (and not for others).
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        project_count = get_permitted_projects_for_user(test_user, permission).count()

        assert (
            project_count == 0
            if permission not in [VIEW_PROJECT, CREATE_ENVIRONMENT]
            else 1
        )

    # Next, let's give some more permissions using `user_permission_group`
    project_permission_using_user_permission_group.permissions.add(CREATE_ENVIRONMENT)
    project_permission_using_user_permission_group.permissions.add(DELETE_FEATURE)

    # And assert again
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        project_count = get_permitted_projects_for_user(test_user, permission).count()

        assert (
            project_count == 0
            if permission not in [VIEW_PROJECT, CREATE_ENVIRONMENT, DELETE_FEATURE]
            else 1
        )


def test_get_permitted_project_for_user__does_not_return_project_for_orphan_group_permission(
    organisation: Organisation,
    project: Project,
    user_permission_group: UserPermissionGroup,
    project_permission_using_user_permission_group: UserPermissionGroupProjectPermission,
    admin_user: FFAdminUser,
    view_project_permission: PermissionModel,
) -> None:
    """
    Specific test to verify that a user no longer has permission to access resources via a group,
    if they no longer belong to the organisation.

    Note that a user should never be a member of a group without being a member of the organisation
    but this test exists to ensure no security holes.
    """

    # Given
    project_permission_using_user_permission_group.permissions.add(
        view_project_permission
    )
    assert (
        get_permitted_projects_for_user(
            user=admin_user, permission_key=VIEW_PROJECT
        ).count()
        == 1
    )

    # When
    # We delete the user organisation to remove the user from the organisation, without
    # allowing any signals / hooks to run.
    UserOrganisation.objects.filter(user=admin_user, organisation=organisation).delete()

    # Then
    assert (
        get_permitted_projects_for_user(
            user=admin_user, permission_key=VIEW_PROJECT
        ).count()
        == 0
    )

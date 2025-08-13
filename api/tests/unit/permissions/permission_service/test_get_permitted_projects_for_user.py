import typing

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
    UserProjectPermission,
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
def test_get_permitted_projects_for_user_returns_the_project_for_project_admin(
    staff_user: FFAdminUser,
    project: Project,
    project_admin: typing.Union[
        UserProjectPermission, UserPermissionGroupProjectPermission
    ],
    project_two: Project,
) -> None:
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert get_permitted_projects_for_user(staff_user, permission).count() == 1


def test_get_permitted_projects_for_user_returns_correct_project(
    staff_user: FFAdminUser,
    project: Project,
    view_project_permission: PermissionModel,
    create_environment_permission: PermissionModel,
    delete_feature_permission: PermissionModel,
    project_permission_using_user_permission: UserProjectPermission,
    project_permission_using_user_permission_group: UserPermissionGroupProjectPermission,
) -> None:
    # First, let's assert that the user does not have access to any project
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        assert get_permitted_projects_for_user(staff_user, permission).count() == 0

    # Next, let's give user some permissions using `user_permission`
    project_permission_using_user_permission.permissions.add(view_project_permission)
    project_permission_using_user_permission.permissions.add(
        create_environment_permission
    )

    # Next, let's assert that the project is returned only for those permissions (and not for others).
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        project_count = get_permitted_projects_for_user(staff_user, permission).count()

        assert (
            project_count == 0
            if permission not in [VIEW_PROJECT, CREATE_ENVIRONMENT]
            else 1
        )

    # Next, let's give some more permissions using `user_permission_group`
    project_permission_using_user_permission_group.permissions.add(
        create_environment_permission
    )
    project_permission_using_user_permission_group.permissions.add(
        delete_feature_permission
    )

    # And assert again
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        project_count = get_permitted_projects_for_user(staff_user, permission).count()

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

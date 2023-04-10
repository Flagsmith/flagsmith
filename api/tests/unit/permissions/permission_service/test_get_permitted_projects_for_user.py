import pytest
from pytest_lazyfixture import lazy_fixture

from permissions.permission_service import get_permitted_projects_for_user
from projects.models import ProjectPermissionModel
from projects.permissions import (
    CREATE_ENVIRONMENT,
    DELETE_FEATURE,
    MANAGE_SEGMENTS,
    VIEW_PROJECT,
)


def test_get_permitted_projects_for_user_returns_all_projects_for_org_admin(
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
        (lazy_fixture("project_admin_via_user_role")),
        (lazy_fixture("project_admin_via_group_role")),
    ],
)
def test_get_permitted_projects_for_user_returns_the_project_for_project_admin(
    test_user, project, project_admin, project_two
):
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert get_permitted_projects_for_user(test_user, permission).count() == 1


def test_get_permitted_projects_for_user_returns_correct_project(
    test_user,
    project,
    project_permission_using_user_permission,
    project_permission_using_user_permission_group,
    project_permission_using_user_role,
    project_permission_using_group_role,
):
    # First, let's assert user does not have access to any project
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        assert get_permitted_projects_for_user(test_user, permission).count() == 0

    # Next, let's give user some permissions using `user_permission`
    project_permission_using_user_permission.permissions.add(VIEW_PROJECT)
    project_permission_using_user_permission.permissions.add(CREATE_ENVIRONMENT)

    # Next, let's assert the project is returned for those permissions(and not for the other)
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

    # Next, let's give more permissions using `user_role`
    project_permission_using_user_role.permissions.add(DELETE_FEATURE)

    # And verify again that we can fetch the project using these permissions
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        project_count = get_permitted_projects_for_user(test_user, permission).count()

        assert (
            project_count == 0
            if permission
            not in [
                VIEW_PROJECT,
                CREATE_ENVIRONMENT,
                DELETE_FEATURE,
            ]
            else 1
        )
    # Finally, let's give permissions using `group_role`
    project_permission_using_group_role.permissions.add(MANAGE_SEGMENTS)

    # And, verify that project is returned for those permission
    for permission in ProjectPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        project_count = get_permitted_projects_for_user(test_user, permission).count()

        assert (
            project_count == 0
            if permission
            not in [
                VIEW_PROJECT,
                CREATE_ENVIRONMENT,
                DELETE_FEATURE,
                MANAGE_SEGMENTS,
            ]
            else 1
        )

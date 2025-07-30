import typing

import pytest
from common.environments.permissions import (
    MANAGE_IDENTITIES,
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]

from environments.models import Environment
from environments.permissions.models import (
    EnvironmentPermissionModel,
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from organisations.models import Organisation
from permissions.models import PermissionModel
from permissions.permission_service import get_permitted_environments_for_user
from projects.models import (
    Project,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from users.models import FFAdminUser, UserPermissionGroup


def test_get_permitted_environments_for_user_returns_all_environments_for_org_admin(  # type: ignore[no-untyped-def]
    admin_user, environment, project, project_two_environment
):
    for permission in EnvironmentPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert (
            get_permitted_environments_for_user(admin_user, project, permission).count()
            == 1
        )


@pytest.mark.parametrize(
    "project_admin",
    [
        (lazy_fixture("project_admin_via_user_permission")),
        (lazy_fixture("project_admin_via_user_permission_group")),
    ],
)
def test_get_permitted_environments_for_user_returns_all_the_environments_for_project_admin(  # noqa: E501
    staff_user: FFAdminUser,
    environment: Environment,
    project: Project,
    project_admin: typing.Union[
        UserProjectPermission, UserPermissionGroupProjectPermission
    ],
    project_two_environment: Environment,
) -> None:
    for permission in EnvironmentPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert (
            get_permitted_environments_for_user(staff_user, project, permission).count()
            == 1
        )


@pytest.mark.parametrize(
    "environment_admin",
    [
        (lazy_fixture("environment_admin_via_user_permission")),
        (lazy_fixture("environment_admin_via_user_permission_group")),
    ],
)
def test_get_permitted_environments_for_user_returns_the_environment_for_environment_admin(  # noqa: E501
    staff_user: FFAdminUser,
    environment: Environment,
    project: Project,
    environment_admin: typing.Union[
        UserEnvironmentPermission, UserPermissionGroupProjectPermission
    ],
    project_two_environment: Environment,
) -> None:
    for permission in EnvironmentPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        # Then
        assert (
            get_permitted_environments_for_user(staff_user, project, permission).count()
            == 1
        )


def test_get_permitted_environments_for_user_returns_correct_environment(
    staff_user: FFAdminUser,
    environment: Environment,
    project_two_environment: Environment,
    project: Project,
    view_environment_permission: PermissionModel,
    update_feature_state_permission: PermissionModel,
    manage_identities_permission: PermissionModel,
    environment_permission_using_user_permission: UserEnvironmentPermission,
    environment_permission_using_user_permission_group: UserPermissionGroupProjectPermission,
) -> None:
    # First, let's assert that the user does not have access to any environment
    for permission in EnvironmentPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        assert (
            get_permitted_environments_for_user(staff_user, project, permission).count()
            == 0
        )
    # Next, let's give user some permissions using `user_permission`
    permissions_as_user = [VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE]
    environment_permission_using_user_permission.permissions.add(
        *[
            PermissionModel.objects.get(key=permission)
            for permission in permissions_as_user
        ]
    )

    # Next, let's assert that the environment is returned only for those permissions (and not for others).
    for permission in EnvironmentPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        environment_count = get_permitted_environments_for_user(
            staff_user, project, permission
        ).count()

        assert environment_count == 0 if permission not in permissions_as_user else 1, (
            f"Failed for permission {permission}"
        )

    # Next, let's give some more permissions using `user_permission_group`
    permissions_as_group = [
        UPDATE_FEATURE_STATE,
        MANAGE_IDENTITIES,
    ]
    environment_permission_using_user_permission_group.permissions.add(
        *[
            PermissionModel.objects.get(key=permission)
            for permission in permissions_as_group
        ]
    )

    # And assert again
    for permission in EnvironmentPermissionModel.objects.all().values_list(
        "key", flat=True
    ):
        environment_count = get_permitted_environments_for_user(
            staff_user, project, permission
        ).count()

        assert (
            environment_count == 0
            if permission not in permissions_as_group + permissions_as_user
            else 1
        )


def test_get_permitted_environments_for_user__does_not_return_environment_for_orphan_group_permission(
    organisation: Organisation,
    project: Project,
    environment: Environment,
    user_permission_group: UserPermissionGroup,
    environment_permission_using_user_permission_group: UserPermissionGroupEnvironmentPermission,
    staff_user: FFAdminUser,
    view_environment_permission: PermissionModel,
) -> None:
    """
    Specific test to verify that a user no longer has permission to access resources via a group,
    if they no longer belong to the organisation.

    Note that a user should never be a member of a group without being a member of the organisation
    but this test exists to ensure no security holes.
    """

    # Given
    staff_user.add_to_group(group=user_permission_group)

    environment_permission_using_user_permission_group.permissions.add(
        view_environment_permission
    )
    assert (
        get_permitted_environments_for_user(
            user=staff_user, project=project, permission_key=VIEW_ENVIRONMENT
        ).count()
        == 1
    )

    # When
    # We delete the user organisation to remove the user from the organisation, without
    # allowing any signals / hooks to run.
    UserOrganisation.objects.filter(user=staff_user, organisation=organisation).delete()

    # Then
    assert (
        get_permitted_environments_for_user(
            user=staff_user, project=project, permission_key=VIEW_ENVIRONMENT
        ).count()
        == 0
    )

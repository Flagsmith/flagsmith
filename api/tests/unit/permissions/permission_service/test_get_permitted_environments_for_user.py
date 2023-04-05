import pytest
from pytest_lazyfixture import lazy_fixture

from environments.permissions.constants import (
    CREATE_CHANGE_REQUEST,
    ENVIRONMENT_PERMISSIONS,
    MANAGE_IDENTITIES,
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
    VIEW_IDENTITIES,
)
from permissions.permission_service import get_permitted_environments_for_user


def test_get_permitted_environments_for_user_returns_all_the_environments_for_org_admin(
    admin_user, environment, project, project_two_environment
):
    # When
    permitted_environments = get_permitted_environments_for_user(
        admin_user, project, VIEW_ENVIRONMENT
    )

    # Then
    assert permitted_environments.count() == 1


@pytest.mark.parametrize(
    "project_admin",
    [
        (lazy_fixture("project_admin_via_user_permission")),
        (lazy_fixture("project_admin_via_user_permission_group")),
        (lazy_fixture("project_admin_via_user_role")),
        (lazy_fixture("project_admin_via_group_role")),
    ],
)
def test_get_permitted_environments_for_user_returns_all_the_environments_for_project_admin(
    test_user, environment, project, project_admin, project_two_environment
):
    # When
    permitted_environments = get_permitted_environments_for_user(
        test_user, project, VIEW_ENVIRONMENT
    )

    # Then
    assert permitted_environments.count() == 1


@pytest.mark.parametrize(
    "environment_admin",
    [
        (lazy_fixture("environment_admin_via_user_permission")),
        (lazy_fixture("environment_admin_via_user_permission_group")),
        (lazy_fixture("environment_admin_via_user_role")),
        (lazy_fixture("environment_admin_via_group_role")),
    ],
)
def test_get_permitted_environments_for_user_returns_the_environments_for_environment_admin(
    test_user, environment, project, environment_admin, project_two_environment
):
    # When
    permitted_environments = get_permitted_environments_for_user(
        test_user, project, VIEW_ENVIRONMENT
    )

    # Then
    assert permitted_environments.count() == 1


# @pytest.mark.parametrize(
#     "environment_permission",
#     [
#         (lazy_fixture("environment_permission_using_user_permission")),
#         (lazy_fixture("environment_permission_using_user_permission_group")),
#         # (lazy_fixture("environment_admin_via_user_role")),
#         # (lazy_fixture("environment_admin_via_group_role")),


#     ],
# )
def test_get_permitted_environments_for_user_returns_correct_environment(
    test_user,
    environment,
    project_two_environment,
    project,
    environment_permission_using_user_permission,
    environment_permission_using_user_permission_group,
    environment_permission_using_user_role,
    environment_permission_using_group_role,
):
    # First, let's assert user does not have access to any environment
    for permission, _ in ENVIRONMENT_PERMISSIONS:
        assert (
            get_permitted_environments_for_user(test_user, project, permission).count()
            == 0
        )
    # Next, let's give user some permissions using `user_permission`
    environment_permission_using_user_permission.permissions.add(VIEW_ENVIRONMENT)
    environment_permission_using_user_permission.permissions.add(UPDATE_FEATURE_STATE)

    # Next, let's assert the environment is returned for those permissions(and not for the other)
    for permission, _ in ENVIRONMENT_PERMISSIONS:
        environment_count = get_permitted_environments_for_user(
            test_user, project, permission
        ).count()

        assert (
            environment_count == 0
            if permission not in [VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE]
            else 1
        )

    # Next, let's give some more permissions using `user_permission_group`
    environment_permission_using_user_permission_group.permissions.add(
        UPDATE_FEATURE_STATE
    )
    environment_permission_using_user_permission_group.permissions.add(
        MANAGE_IDENTITIES
    )

    # And assert again
    for permission, _ in ENVIRONMENT_PERMISSIONS:
        environment_count = get_permitted_environments_for_user(
            test_user, project, permission
        ).count()

        assert (
            environment_count == 0
            if permission
            not in [VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE, MANAGE_IDENTITIES]
            else 1
        )

    # Next, let's give more permissions using `user_role`
    environment_permission_using_user_role.permissions.add(MANAGE_IDENTITIES)
    environment_permission_using_user_role.permissions.add(VIEW_IDENTITIES)

    # And verify again that we can fetch the environment using these permissions
    for permission, _ in ENVIRONMENT_PERMISSIONS:
        environment_count = get_permitted_environments_for_user(
            test_user, project, permission
        ).count()

        assert (
            environment_count == 0
            if permission
            not in [
                VIEW_ENVIRONMENT,
                UPDATE_FEATURE_STATE,
                MANAGE_IDENTITIES,
                VIEW_IDENTITIES,
            ]
            else 1
        )
    # Finally, let's give permissions using `group_role`
    environment_permission_using_group_role.permissions.add(CREATE_CHANGE_REQUEST)

    # And, verify that environment is returned for those permission
    for permission, _ in ENVIRONMENT_PERMISSIONS:
        environment_count = get_permitted_environments_for_user(
            test_user, project, permission
        ).count()

        assert (
            environment_count == 0
            if permission
            not in [
                VIEW_ENVIRONMENT,
                UPDATE_FEATURE_STATE,
                MANAGE_IDENTITIES,
                VIEW_IDENTITIES,
                CREATE_CHANGE_REQUEST,
            ]
            else 1
        )

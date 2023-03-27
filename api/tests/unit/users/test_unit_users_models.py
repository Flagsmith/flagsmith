from environments.permissions.constants import VIEW_ENVIRONMENT


def test_get_permitted_environments_returns_environment_added_by_user_role(
    test_user, user_role, role_view_environment_permission, environment, project
):
    # When
    permitted_environments = test_user.get_permitted_environments(
        VIEW_ENVIRONMENT, project
    )

    # Then
    assert environment in permitted_environments


def test_get_permitted_environments_returns_environment_added_by_group_role(
    test_user,
    group_role,
    role_view_environment_permission,
    environment,
    project,
    user_permission_group,
):
    # Given
    user_permission_group.users.add(test_user)

    # When
    permitted_environments = test_user.get_permitted_environments(
        VIEW_ENVIRONMENT, project
    )

    # Then
    assert environment in permitted_environments


def test_get_permitted_projects_returns_projects_added_by_user_role(
    test_user, user_role, role_view_project_permission, project
):
    # When
    permitted_projects = test_user.get_permitted_projects(["VIEW_PROJECT"])

    # Then
    assert project in permitted_projects


def test_get_permitted_projects_returns_projects_added_by_group_role(
    test_user,
    group_role,
    role_view_project_permission,
    project,
    user_permission_group,
):
    # Given
    user_permission_group.users.add(test_user)

    # When
    permitted_projects = test_user.get_permitted_projects(["VIEW_PROJECT"])

    # Then
    assert project in permitted_projects


def test_is_project_admin_returns_true_if_user_role_is_project_admin(
    test_user, user_role, project, role_project_admin_permission
):
    # When
    result = test_user.is_project_admin(project)

    # Then
    assert result is True


def test_is_project_admin_returns_true_if_user_group_role_is_project_admin(
    test_user,
    group_role,
    project,
    role_project_admin_permission,
    user_permission_group,
):
    # Given
    user_permission_group.users.add(test_user)

    # When
    result = test_user.is_project_admin(project)

    # Then
    assert result is True

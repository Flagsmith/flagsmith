import pytest


@pytest.fixture
def project_permission_using_user_permission(user_project_permission):
    return user_project_permission


@pytest.fixture
def project_admin_via_user_permission(project_permission_using_user_permission):
    project_permission_using_user_permission.admin = True
    project_permission_using_user_permission.save()

    return project_permission_using_user_permission


@pytest.fixture
def project_permission_using_user_permission_group(
    user_project_permission_group, user_permission_group, test_user
):
    user_permission_group.users.add(test_user)
    return user_project_permission_group


@pytest.fixture
def project_admin_via_user_permission_group(
    project_permission_using_user_permission_group,
):
    project_permission_using_user_permission_group.admin = True
    project_permission_using_user_permission_group.save()

    return project_permission_using_user_permission_group


@pytest.fixture
def environment_admin_via_user_permission(test_user, user_environment_permission):
    user_environment_permission.admin = True
    user_environment_permission.save()

    return user_environment_permission


@pytest.fixture
def environment_permission_using_user_permission(user_environment_permission):
    return user_environment_permission


@pytest.fixture
def environment_admin_via_user_permission_group(
    user_environment_permission_group, test_user, user_permission_group
):
    user_permission_group.users.add(test_user)

    user_environment_permission_group.admin = True
    user_environment_permission_group.save()

    return user_environment_permission_group


@pytest.fixture
def environment_permission_using_user_permission_group(
    user_environment_permission_group, user_permission_group, test_user
):
    user_permission_group.users.add(test_user)
    return user_environment_permission_group

import pytest

from environments.models import Environment
from organisations.roles.models import RoleOrganisationPermission
from projects.models import Project


@pytest.fixture
def role_organisation_permission(role, organisation):
    return RoleOrganisationPermission.objects.create(role=role)


@pytest.fixture()
def project_two(organisation):
    return Project.objects.create(name="Test Project Two", organisation=organisation)


@pytest.fixture
def project_two_environment(project_two):
    return Environment.objects.create(name="Test Environment Two", project=project_two)


@pytest.fixture
def project_admin_via_user_permission(test_user, user_project_permission):
    user_project_permission.admin = True
    user_project_permission.save()

    return user_project_permission.user


@pytest.fixture
def project_admin_via_user_permission_group(
    user_project_permission_group, test_user, user_permission_group
):
    user_permission_group.users.add(test_user)

    user_project_permission_group.admin = True
    user_project_permission_group.save()

    return test_user


@pytest.fixture
def project_admin_via_user_role(role_project_permission, user_role, test_user):
    role_project_permission.admin = True
    role_project_permission.save()

    return test_user


@pytest.fixture
def project_admin_via_group_role(
    role_project_permission, group_role, user_permission_group, test_user
):
    role_project_permission.admin = True
    role_project_permission.save()

    user_permission_group.users.add(test_user)

    return role_project_permission


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


@pytest.fixture
def environment_admin_via_user_role(role_environment_permission, user_role):
    role_environment_permission.admin = True
    role_environment_permission.save()

    return role_environment_permission


@pytest.fixture
def environment_permission_using_user_role(role_environment_permission, user_role):
    return role_environment_permission


@pytest.fixture
def environment_permission_using_group_role(
    role_environment_permission, user_permission_group, test_user
):
    user_permission_group.users.add(test_user)
    return role_environment_permission


@pytest.fixture
def environment_admin_via_group_role(
    role_environment_permission, group_role, user_permission_group, test_user
):
    role_environment_permission.admin = True
    role_environment_permission.save()

    user_permission_group.users.add(test_user)

    return role_environment_permission

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
def project_permission_using_user_role(
    role_project_permission,
    user_role,
):
    return role_project_permission


@pytest.fixture
def project_admin_via_user_role(project_permission_using_user_role):
    project_permission_using_user_role.admin = True
    project_permission_using_user_role.save()

    return project_permission_using_user_role


@pytest.fixture
def project_permission_using_group_role(
    user_permission_group, test_user, role_project_permission, group_role
):
    user_permission_group.users.add(test_user)
    return role_project_permission


@pytest.fixture
def project_admin_via_group_role(project_permission_using_group_role):
    project_permission_using_group_role.admin = True
    project_permission_using_group_role.save()

    return project_permission_using_group_role


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

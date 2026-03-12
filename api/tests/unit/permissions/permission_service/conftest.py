import pytest

from environments.models import Environment
from environments.permissions.models import (
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from projects.models import UserPermissionGroupProjectPermission
from users.models import FFAdminUser, UserPermissionGroup


@pytest.fixture
def project_permission_using_user_permission(user_project_permission):  # type: ignore[no-untyped-def]
    return user_project_permission


@pytest.fixture
def project_admin_via_user_permission(project_permission_using_user_permission):  # type: ignore[no-untyped-def]
    project_permission_using_user_permission.admin = True
    project_permission_using_user_permission.save()

    return project_permission_using_user_permission


@pytest.fixture
def project_permission_using_user_permission_group(
    user_project_permission_group: UserPermissionGroupProjectPermission,
    user_permission_group: UserPermissionGroup,
    staff_user: FFAdminUser,
) -> UserPermissionGroupProjectPermission:
    user_permission_group.users.add(staff_user)
    return user_project_permission_group


@pytest.fixture
def project_admin_via_user_permission_group(  # type: ignore[no-untyped-def]
    project_permission_using_user_permission_group,
):
    project_permission_using_user_permission_group.admin = True
    project_permission_using_user_permission_group.save()

    return project_permission_using_user_permission_group


@pytest.fixture
def environment_admin_via_user_permission(
    staff_user: FFAdminUser,
    environment: Environment,  # Explicitly depend on environment to ensure same instance
    user_environment_permission: UserEnvironmentPermission,
) -> UserEnvironmentPermission:
    user_environment_permission.admin = True
    user_environment_permission.save()

    return user_environment_permission


@pytest.fixture
def environment_permission_using_user_permission(user_environment_permission):  # type: ignore[no-untyped-def]
    return user_environment_permission


@pytest.fixture
def environment_admin_via_user_permission_group(
    user_environment_permission_group: UserPermissionGroupEnvironmentPermission,
    staff_user: FFAdminUser,
    user_permission_group: UserPermissionGroup,
    environment: Environment,  # Explicitly depend on environment to ensure same instance
) -> UserPermissionGroupEnvironmentPermission:
    user_permission_group.users.add(staff_user)

    user_environment_permission_group.admin = True
    user_environment_permission_group.save()

    return user_environment_permission_group


@pytest.fixture
def environment_permission_using_user_permission_group(
    user_environment_permission_group: UserPermissionGroupEnvironmentPermission,
    user_permission_group: UserPermissionGroup,
    staff_user: FFAdminUser,
) -> UserPermissionGroupEnvironmentPermission:
    user_permission_group.users.add(staff_user)
    return user_environment_permission_group

import pytest

from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from environments.permissions.models import (
    EnvironmentPermissionModel,
    UserEnvironmentPermission,
)
from projects.models import ProjectPermissionModel, UserProjectPermission


@pytest.fixture()
def environment_one_viewer_user(
    organisation_one_user,
    organisation_one_project_one,
    organisation_one_project_one_environment_one,
):
    view_project_permission = ProjectPermissionModel.objects.get(key="VIEW_PROJECT")
    user_project_permission = UserProjectPermission.objects.create(
        user=organisation_one_user, project=organisation_one_project_one
    )
    user_project_permission.permissions.add(view_project_permission)

    view_environment_permission = EnvironmentPermissionModel.objects.get(
        key=VIEW_ENVIRONMENT
    )
    user_environment_permission = UserEnvironmentPermission.objects.create(
        user=organisation_one_user,
        environment=organisation_one_project_one_environment_one,
    )
    user_environment_permission.permissions.add(view_environment_permission)
    return organisation_one_user


@pytest.fixture()
def environment_one_feature_state_updater_user(
    organisation_one_project_one_environment_one, environment_one_viewer_user
):
    update_feature_state_permission = EnvironmentPermissionModel.objects.get(
        key=UPDATE_FEATURE_STATE
    )
    user_environment_permission = UserEnvironmentPermission.objects.create(
        user=environment_one_viewer_user,
        environment=organisation_one_project_one_environment_one,
    )
    user_environment_permission.permissions.add(update_feature_state_permission)
    return environment_one_viewer_user


@pytest.fixture()
def environment_one_admin_user(
    organisation_one_project_one_environment_one, django_user_model
):
    environment_admin_user = django_user_model.objects.create(
        email="environmentadminuser@example.com"
    )
    UserEnvironmentPermission.objects.create(
        user=environment_admin_user,
        environment=organisation_one_project_one_environment_one,
        admin=True,
    )
    return environment_admin_user

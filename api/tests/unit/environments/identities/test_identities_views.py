from django.urls import reverse
from rest_framework import status

from environments.permissions.constants import (
    MANAGE_IDENTITIES,
    VIEW_ENVIRONMENT,
)
from environments.permissions.models import UserEnvironmentPermission
from permissions.models import PermissionModel
from projects.models import UserProjectPermission


def test_user_with_manage_identities_permission_can_retrieve_identity(
    environment, identity, django_user_model, api_client
):
    # Given
    user = django_user_model.objects.create(email="user@example.com")
    api_client.force_authenticate(user)

    view_environment_permission = PermissionModel.objects.get(key=VIEW_ENVIRONMENT)
    manage_identities_permission = PermissionModel.objects.get(key=MANAGE_IDENTITIES)
    view_project_permission = PermissionModel.objects.get(key="VIEW_PROJECT")

    user_environment_permission = UserEnvironmentPermission.objects.create(
        user=user, environment=environment
    )
    user_environment_permission.permissions.add(
        view_environment_permission, manage_identities_permission
    )

    user_project_permission = UserProjectPermission.objects.create(
        user=user, project=environment.project
    )
    user_project_permission.permissions.add(view_project_permission)

    url = reverse(
        "api-v1:environments:environment-identities-detail",
        args=(environment.api_key, identity.id),
    )

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

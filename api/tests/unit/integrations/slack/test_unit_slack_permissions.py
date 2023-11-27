from unittest import mock

from environments.permissions.models import UserEnvironmentPermission
from integrations.slack.permissions import OauthInitPermission

mock_view = mock.MagicMock()


def test_oauth_init_permission_with_non_environment_admin_user(
    environment, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    mock_request = rf.get("/url")
    mock_request.user = user

    mock_view.kwargs = {"environment_api_key": environment.api_key}
    # When
    oauth_init_permission = OauthInitPermission()
    # Then
    assert oauth_init_permission.has_permission(mock_request, mock_view) is False


def test_oauth_init_permission_with_environment_admin_user(
    environment, django_user_model, rf
):
    # Given
    mock_request = rf.get("/url")
    user = django_user_model.objects.create(username="test_user")
    mock_view.kwargs = {"environment_api_key": environment.api_key}
    mock_request.user = user
    UserEnvironmentPermission.objects.create(
        user=user, admin=True, environment=environment
    )
    # When
    oauth_init_permission = OauthInitPermission()
    # Then
    assert oauth_init_permission.has_permission(mock_request, mock_view) is True

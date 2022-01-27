from unittest import mock

from environments.permissions.models import UserEnvironmentPermission
from organisations.models import OrganisationRole
from webhooks.permissions import TriggerSampleWebhookPermission


def test_has_permission_returns_false_for_org_webhook_if_user_is_not_an_admin(
    organisation, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    mock_request = rf.get("/url")
    mock_request.user = user
    mock_view = mock.MagicMock(basename="organisation-webhooks")
    permission_class = TriggerSampleWebhookPermission()

    # Then
    assert permission_class.has_permission(mock_request, mock_view) is False


def test_has_permission_returns_true_for_org_webhook_if_user_is_an_admin(
    organisation, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    user.add_organisation(organisation, role=OrganisationRole.ADMIN)
    mock_request = rf.get("/url")
    mock_request.user = user
    mock_view = mock.MagicMock(basename="organisation-webhooks")
    permission_class = TriggerSampleWebhookPermission()

    # Then
    assert permission_class.has_permission(mock_request, mock_view) is True


def test_has_permission_returns_false_for_env_webhook_if_user_is_not_an_admin(
    environment, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    mock_request = rf.get("/url")
    mock_request.user = user
    mock_view = mock.MagicMock(basename="environments-webhooks")
    permission_class = TriggerSampleWebhookPermission()

    # Then
    assert permission_class.has_permission(mock_request, mock_view) is False


def test_has_permission_returns_true_for_env_webhook_if_user_is_an_admin(
    environment, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    UserEnvironmentPermission.objects.create(
        user=user, admin=True, environment=environment
    )
    mock_request = rf.get("/url")
    mock_request.user = user

    mock_view = mock.MagicMock(basename="environments-webhooks")
    permission_class = TriggerSampleWebhookPermission()

    # Then
    assert permission_class.has_permission(mock_request, mock_view) is True

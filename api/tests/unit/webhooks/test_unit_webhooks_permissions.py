from unittest import mock

from environments.permissions.models import UserEnvironmentPermission
from organisations.models import OrganisationRole
from webhooks.permissions import TriggerSampleWebhookPermission


def test_has_permission_returns_false_for_org_webhook_if_user_is_not_an_admin(  # type: ignore[no-untyped-def]
    organisation, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    mock_request = rf.get("/url")
    mock_request.user = user
    mock_view = mock.MagicMock(
        basename="organisation-webhooks",
        kwargs={"organisation_pk": organisation.id},
    )
    permission_class = TriggerSampleWebhookPermission()

    # Then
    assert permission_class.has_permission(mock_request, mock_view) is False  # type: ignore[no-untyped-call]


def test_has_permission_returns_true_for_org_webhook_if_user_is_an_admin(  # type: ignore[no-untyped-def]
    organisation, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    user.add_organisation(organisation, role=OrganisationRole.ADMIN)
    mock_request = rf.get("/url")
    mock_request.user = user
    mock_view = mock.MagicMock(
        basename="organisation-webhooks",
        kwargs={"organisation_pk": organisation.id},
    )
    permission_class = TriggerSampleWebhookPermission()

    # Then
    assert permission_class.has_permission(mock_request, mock_view) is True  # type: ignore[no-untyped-call]


def test_has_permission_returns_false_for_env_webhook_if_user_is_not_an_admin(  # type: ignore[no-untyped-def]
    environment, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    mock_request = rf.get("/url")
    mock_request.user = user
    mock_view = mock.MagicMock(
        basename="environments-webhooks",
        kwargs={"environment_api_key": environment.api_key},
    )
    permission_class = TriggerSampleWebhookPermission()

    # Then
    assert permission_class.has_permission(mock_request, mock_view) is False  # type: ignore[no-untyped-call]


def test_has_permission_returns_true_for_env_webhook_if_user_is_an_admin(  # type: ignore[no-untyped-def]
    environment, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    UserEnvironmentPermission.objects.create(
        user=user, admin=True, environment=environment
    )
    mock_request = rf.get("/url")
    mock_request.user = user

    mock_view = mock.MagicMock(
        basename="environments-webhooks",
        kwargs={"environment_api_key": environment.api_key},
    )
    permission_class = TriggerSampleWebhookPermission()

    # Then
    assert permission_class.has_permission(mock_request, mock_view) is True  # type: ignore[no-untyped-call]

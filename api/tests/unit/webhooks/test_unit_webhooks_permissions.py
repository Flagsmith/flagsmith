from unittest import mock

from django.test import RequestFactory
from rest_framework.request import Request

from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from organisations.models import OrganisationRole
from users.models import FFAdminUser
from webhooks.permissions import TriggerSampleWebhookPermission


def test_trigger_sample_webhook_permission__org_webhook_non_admin_user__returns_false(  # type: ignore[no-untyped-def]
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

    # When
    result = permission_class.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


def test_trigger_sample_webhook_permission__org_webhook_admin_user__returns_true(  # type: ignore[no-untyped-def]
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

    # When
    result = permission_class.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_trigger_sample_webhook_permission__env_webhook_non_admin_user__returns_false(  # type: ignore[no-untyped-def]
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

    # When
    result = permission_class.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


def test_trigger_sample_webhook_permission__env_webhook_admin_user__returns_true(
    environment: Environment,
    staff_user: FFAdminUser,
    rf: RequestFactory,
) -> None:
    # Given
    UserEnvironmentPermission.objects.create(
        user=staff_user, admin=True, environment=environment
    )
    mock_request = rf.get("/url")
    mock_request.user = staff_user

    mock_view = mock.MagicMock(
        basename="environments-webhooks",
        kwargs={"environment_api_key": environment.api_key},
    )
    permission_class = TriggerSampleWebhookPermission()

    # When
    result = permission_class.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_trigger_sample_webhook_permission__non_webhook_test_basename__ignores_payload_scope(  # type: ignore[no-untyped-def]  # noqa: E501
    organisation, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    user.add_organisation(organisation, role=OrganisationRole.ADMIN)
    mock_request = rf.post("/v1/webhooks/test")
    mock_request.user = user
    mock_request.data = {
        "webhook_url": "http://test.webhook.com",
        "secret": "some-secret",
        "payload": {"test": "data"},
        "scope": {"type": "organisation", "id": organisation.id},
    }

    mock_view = mock.MagicMock(basename="environments-webhooks", kwargs={})
    permission_class = TriggerSampleWebhookPermission()

    # When
    result = permission_class.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is False


def test_trigger_sample_webhook_permission__webhook_test_org_admin__returns_true(  # type: ignore[no-untyped-def]
    organisation, django_user_model, rf
):
    # Given
    user = django_user_model.objects.create(username="test_user")
    user.add_organisation(organisation, role=OrganisationRole.ADMIN)
    mock_request = rf.post("/v1/webhooks/test")
    mock_request.user = user
    mock_request.data = {
        "webhook_url": "http://test.webhook.com",
        "secret": "some-secret",
        "payload": {"test": "data"},
        "scope": {"type": "organisation", "id": organisation.id},
    }

    mock_view = mock.MagicMock(basename="webhooks", action="test", kwargs={})
    permission_class = TriggerSampleWebhookPermission()

    # When
    result = permission_class.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True


def test_trigger_sample_webhook_permission__webhook_test_env_admin__returns_true(
    environment: Environment,
    staff_user: FFAdminUser,
    user_environment_permission: UserEnvironmentPermission,
) -> None:
    # Given
    user_environment_permission.admin = True
    user_environment_permission.save()

    mock_request = mock.MagicMock(spec=Request)
    mock_request.user = staff_user
    mock_request.data = {
        "webhook_url": "http://test.webhook.com",
        "secret": "some-secret",
        "payload": {"test": "data"},
        "scope": {"type": "environment", "id": environment.api_key},
    }

    mock_view = mock.MagicMock(basename="webhooks", action="test", kwargs={})
    permission_class = TriggerSampleWebhookPermission()

    # When
    result = permission_class.has_permission(mock_request, mock_view)  # type: ignore[no-untyped-call]

    # Then
    assert result is True

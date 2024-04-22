import json
from datetime import datetime, timedelta
from typing import Type
from unittest import mock
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.db.models import Model
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from pytest_lazyfixture import lazy_fixture
from pytest_mock import MockerFixture
from pytz import UTC
from rest_framework import status
from rest_framework.test import APIClient, override_settings

from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from features.models import Feature
from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.invites.models import Invite
from organisations.models import (
    OranisationAPIUsageNotification,
    Organisation,
    OrganisationRole,
    OrganisationSubscriptionInformationCache,
    OrganisationWebhook,
    Subscription,
)
from organisations.permissions.models import UserOrganisationPermission
from organisations.permissions.permissions import CREATE_PROJECT
from organisations.subscriptions.constants import (
    CHARGEBEE,
    MAX_API_CALLS_IN_FREE_PLAN,
    MAX_SEATS_IN_FREE_PLAN,
    SUBSCRIPTION_BILLING_STATUS_ACTIVE,
    SUBSCRIPTION_BILLING_STATUS_DUNNING,
)
from projects.models import Project, UserProjectPermission
from segments.models import Segment
from users.models import (
    FFAdminUser,
    UserPermissionGroup,
    UserPermissionGroupMembership,
)

User = get_user_model()


def test_should_return_organisation_list_when_requested(
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    # When
    response = staff_client.get("/api/v1/organisations/")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert "count" in response.data and response.data["count"] == 1
    assert response.data["results"][0]["role"] == "USER"
    assert response.data["results"][0]["name"] == organisation.name


def test_non_superuser_can_create_new_organisation_by_default(
    staff_client: APIClient,
) -> None:
    # Given
    org_name = "Test create org"
    webhook_notification_email = "test@email.com"
    url = reverse("api-v1:organisations:organisation-list")
    data = {
        "name": org_name,
        "webhook_notification_email": webhook_notification_email,
    }

    # When
    response = staff_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        Organisation.objects.get(name=org_name).webhook_notification_email
        == webhook_notification_email
    )


@override_settings(RESTRICT_ORG_CREATE_TO_SUPERUSERS=True)
def test_create_new_orgnisation_returns_403_with_non_superuser(
    staff_client: APIClient,
) -> None:
    # Given
    org_name = "Test create org"
    url = reverse("api-v1:organisations:organisation-list")
    data = {
        "name": org_name,
    }

    # When
    response = staff_client.post(url, data=data)
    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert (
        "You do not have permission to perform this action."
        == response.json()["detail"]
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_should_update_organisation_data(
    client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    new_organisation_name = "new test org"
    url = reverse("api-v1:organisations:organisation-detail", args=[organisation.pk])
    data = {"name": new_organisation_name, "restrict_project_create_to_admin": True}

    # When
    response = client.put(url, data=data)

    # Then
    organisation.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert organisation.name == new_organisation_name
    assert organisation.restrict_project_create_to_admin is True


def test_should_invite_users_to_organisation(
    settings: SettingsWrapper,
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None

    url = reverse("api-v1:organisations:organisation-invite", args=[organisation.pk])
    data = {"emails": ["test@example.com"]}

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert Invite.objects.filter(email="test@example.com").exists()


def test_should_fail_if_invite_exists_already(
    settings: SettingsWrapper,
    admin_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None

    email = "test_2@example.com"
    data = {"emails": [email]}
    url = reverse("api-v1:organisations:organisation-invite", args=[organisation.pk])

    # When
    response_success = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    response_fail = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response_success.status_code == status.HTTP_201_CREATED
    assert response_fail.status_code == status.HTTP_400_BAD_REQUEST
    assert Invite.objects.filter(email=email, organisation=organisation).count() == 1


def test_should_return_all_invites_and_can_resend(
    settings: SettingsWrapper,
    admin_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None

    invite_1 = Invite.objects.create(
        email="test_1@example.com", organisation=organisation
    )
    Invite.objects.create(email="test_2@example.com", organisation=organisation)

    # When
    invite_list_response = admin_client.get(
        "/api/v1/organisations/%s/invites/" % organisation.id
    )
    invite_resend_response = admin_client.post(
        "/api/v1/organisations/%s/invites/%s/resend/" % (organisation.id, invite_1.id)
    )

    # Then
    assert invite_list_response.status_code == status.HTTP_200_OK
    assert invite_resend_response.status_code == status.HTTP_200_OK


def test_remove_user_from_an_organisation_also_removes_from_group(
    organisation: Organisation,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    staff_user: FFAdminUser,
) -> None:
    # Given
    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    # Add users to the group
    group.users.add(staff_user)
    group.users.add(admin_user)
    url = reverse(
        "api-v1:organisations:organisation-remove-users", args=[organisation.pk]
    )

    data = [{"id": staff_user.pk}]

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert organisation not in staff_user.organisations.all()
    assert group not in staff_user.permission_groups.all()
    # Test that other users are still part of the group
    assert group in admin_user.permission_groups.all()


def test_remove_user_from_an_organisation_also_removes_users_environment_and_project_permission(
    organisation: Organisation,
    admin_client: APIClient,
    admin_user: FFAdminUser,
) -> None:
    # Given
    # Now, let's create a project
    project_name = "org_remove_test"
    project_create_url = reverse("api-v1:projects:project-list")
    data = {"name": project_name, "organisation": organisation.id}

    response = admin_client.post(project_create_url, data=data)
    project_id = response.data["id"]

    # Next, let's create an environment
    url = reverse("api-v1:environments:environment-list")
    data = {"name": "Test environment", "project": project_id}
    response = admin_client.post(url, data=data)
    environment_id = response.data["id"]

    url = reverse(
        "api-v1:organisations:organisation-remove-users", args=[organisation.pk]
    )

    data = [{"id": admin_user.id}]

    # Next, let's remove the user from the organisation
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        UserProjectPermission.objects.filter(
            project__id=project_id, user=admin_user
        ).count()
        == 0
    )
    assert (
        UserEnvironmentPermission.objects.filter(
            user=admin_user, environment__id=environment_id
        ).count()
        == 0
    )


def test_can_invite_user_as_admin(
    settings: SettingsWrapper,
    admin_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None

    url = reverse("api-v1:organisations:organisation-invite", args=[organisation.pk])
    invited_email = "test@example.com"

    data = {"invites": [{"email": invited_email, "role": OrganisationRole.ADMIN.name}]}

    # When
    admin_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert Invite.objects.filter(email=invited_email).exists()
    assert Invite.objects.get(email=invited_email).role == OrganisationRole.ADMIN.name


def test_can_invite_user_as_user(
    settings: SettingsWrapper,
    admin_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None

    url = reverse("api-v1:organisations:organisation-invite", args=[organisation.pk])
    invited_email = "test@example.com"

    data = {"invites": [{"email": invited_email, "role": OrganisationRole.USER.name}]}

    # When
    admin_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert Invite.objects.filter(email=invited_email).exists()

    # and
    assert Invite.objects.get(email=invited_email).role == OrganisationRole.USER.name


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("staff_client")],
)
def test_user_can_get_projects_for_an_organisation(
    organisation: Organisation,
    client: APIClient,
    project: Project,
) -> None:
    # Given
    url = reverse("api-v1:organisations:organisation-projects", args=[organisation.pk])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["uuid"] == str(project.uuid)
    assert response.data[0]["name"] == project.name


@mock.patch("app_analytics.influxdb_wrapper.influxdb_client")
def test_should_get_usage_for_organisation(
    mock_influxdb_client: MagicMock,
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:organisations:organisation-usage", args=[organisation.pk])

    influx_org = settings.INFLUXDB_ORG
    read_bucket = settings.INFLUXDB_BUCKET + "_downsampled_15m"
    expected_query = (
        (
            f'from(bucket:"{read_bucket}") '
            "|> range(start: -30d, stop: now()) "
            '|> filter(fn:(r) => r._measurement == "api_call")         '
            '|> filter(fn: (r) => r["_field"] == "request_count")         '
            f'|> filter(fn: (r) => r["organisation_id"] == "{organisation.id}") '
            '|> drop(columns: ["organisation", "project", "project_id", '
            '"environment", "environment_id"])'
            "|> sum()"
        )
        .replace(" ", "")
        .replace("\n", "")
    )

    # When
    response = admin_client.get(url, content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    mock_influxdb_client.query_api.return_value.query.assert_called_once()

    call = mock_influxdb_client.query_api.return_value.query.mock_calls[0]
    assert call[2]["org"] == influx_org
    assert call[2]["query"].replace(" ", "").replace("\n", "") == expected_query


@mock.patch("organisations.serializers.get_subscription_data_from_hosted_page")
def test_update_subscription_gets_subscription_data_from_chargebee(
    mock_get_subscription_data: MagicMock,
    settings: SettingsWrapper,
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    settings.ENABLE_CHARGEBEE = True

    # Given
    url = reverse(
        "api-v1:organisations:organisation-update-subscription",
        args=[organisation.pk],
    )

    hosted_page_id = "some-id"
    data = {"hosted_page_id": hosted_page_id}

    customer_id = "customer-id"

    subscription_id = "subscription-id"
    mock_get_subscription_data.return_value = {
        "subscription_id": subscription_id,
        "plan": "plan-id",
        "max_seats": 3,
        "subscription_date": datetime.now(tz=UTC),
        "customer_id": customer_id,
    }

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK

    organisation.refresh_from_db()
    mock_get_subscription_data.assert_called_with(hosted_page_id=hosted_page_id)

    assert organisation.has_paid_subscription()
    assert organisation.subscription.subscription_id == subscription_id
    assert organisation.subscription.customer_id == customer_id


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_delete_organisation(
    organisation: Organisation,
    client: APIClient,
    project: Project,
    environment: Environment,
    feature: Feature,
    segment: Segment,
) -> None:
    # Given
    url = reverse("api-v1:organisations:organisation-detail", args=[organisation.id])

    # When
    response = client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Assure models are not actually deleted but soft deleted or
    # related to a soft deleted object.
    organisation.refresh_from_db()
    assert organisation.id
    assert organisation.deleted_at is not None

    project.refresh_from_db()
    assert project.id
    environment.refresh_from_db()
    assert environment.id
    feature.refresh_from_db()
    assert feature.id
    segment.refresh_from_db()
    assert segment.id


@mock.patch("organisations.serializers.get_hosted_page_url_for_subscription_upgrade")
def test_get_hosted_page_url_for_subscription_upgrade(
    mock_get_hosted_page_url: MagicMock,
    organisation: Organisation,
    admin_client: APIClient,
    subscription: Subscription,
) -> None:
    # Given
    subscription.subscription_id = "sub-id"
    subscription.save()

    url = reverse(
        "api-v1:organisations:organisation-get-hosted-page-url-for-subscription-upgrade",
        args=[organisation.id],
    )

    expected_url = "https://some.url.com/hosted/page"
    mock_get_hosted_page_url.return_value = expected_url

    plan_id = "plan-id"

    # When
    response = admin_client.post(
        url, data=json.dumps({"plan_id": plan_id}), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["url"] == expected_url
    mock_get_hosted_page_url.assert_called_once_with(
        subscription_id=subscription.subscription_id, plan_id=plan_id
    )


def test_get_organisation_permissions(
    staff_client: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:organisations:organisation-permissions")

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


def test_get_my_permissions_for_non_admin(
    organisation: Organisation,
    staff_client: APIClient,
    staff_user: FFAdminUser,
) -> None:
    # Given
    user_permission = UserOrganisationPermission.objects.create(
        user=staff_user, organisation=organisation
    )
    user_permission.add_permission(CREATE_PROJECT)

    url = reverse(
        "api-v1:organisations:organisation-my-permissions", args=[organisation.id]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["permissions"] == [CREATE_PROJECT]
    assert response.data["admin"] is False


def test_get_my_permissions_for_admin(
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-my-permissions", args=[organisation.id]
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["permissions"] == []
    assert response.data["admin"] is True


@mock.patch("organisations.chargebee.webhook_handlers.extract_subscription_metadata")
def test_chargebee_webhook(
    mock_extract_subscription_metadata: MagicMock,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    subscription: Subscription,
) -> None:
    # Given
    seats = 3
    api_calls = 100
    mock_extract_subscription_metadata.return_value = ChargebeeObjMetadata(
        seats=seats,
        api_calls=api_calls,
        projects=None,
        chargebee_email=staff_user.email,
    )
    subscription.subscription_id = "subscription-id"
    subscription.save()
    data = {
        "content": {
            "subscription": {
                "status": "active",
                "id": subscription.subscription_id,
                "current_term_start": 1699630389,
                "current_term_end": 1702222389,
            },
            "customer": {"email": staff_user.email},
        }
    }

    url = reverse("api-v1:chargebee-webhook")
    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    subscription.refresh_from_db()
    subscription_cache = OrganisationSubscriptionInformationCache.objects.get(
        organisation=subscription.organisation
    )
    assert subscription_cache.current_billing_term_ends_at == datetime(
        2023, 12, 10, 15, 33, 9, tzinfo=timezone.utc
    )
    assert subscription_cache.current_billing_term_starts_at == datetime(
        2023, 11, 10, 15, 33, 9, tzinfo=timezone.utc
    )
    assert subscription_cache.allowed_projects is None
    assert subscription_cache.allowed_30d_api_calls == api_calls
    assert subscription_cache.allowed_seats == seats


@mock.patch("organisations.models.cancel_chargebee_subscription")
def test_when_subscription_is_set_to_non_renewing_then_cancellation_date_set_and_alert_sent(
    mocked_cancel_chargebee_subscription: MagicMock,
    subscription: Subscription,
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    cancellation_date = datetime.now(tz=UTC) + timedelta(days=1)
    current_term_end = int(datetime.timestamp(cancellation_date))
    subscription.subscription_id = "subscription-id"
    subscription.save()
    data = {
        "content": {
            "subscription": {
                "status": "non_renewing",
                "id": subscription.subscription_id,
                "current_term_end": current_term_end,
            },
            "customer": {"email": staff_user.email},
        }
    }
    url = reverse("api-v1:chargebee-webhook")

    # When
    staff_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    subscription.refresh_from_db()
    assert subscription.cancellation_date == datetime.utcfromtimestamp(
        current_term_end
    ).replace(tzinfo=timezone.utc)

    # and
    assert len(mail.outbox) == 1
    mocked_cancel_chargebee_subscription.assert_not_called()


def test_when_subscription_is_cancelled_then_cancellation_date_set_and_alert_sent(
    subscription: Subscription,
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    cancellation_date = datetime.now(tz=UTC) + timedelta(days=1)
    current_term_end = int(datetime.timestamp(cancellation_date))
    subscription.subscription_id = "subscription-id"
    subscription.save()
    data = {
        "content": {
            "subscription": {
                "status": "cancelled",
                "id": subscription.subscription_id,
                "current_term_end": current_term_end,
            },
            "customer": {"email": staff_user.email},
        }
    }
    url = reverse("api-v1:chargebee-webhook")

    # When
    staff_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    subscription.refresh_from_db()
    assert subscription.cancellation_date == datetime.utcfromtimestamp(
        current_term_end
    ).replace(tzinfo=timezone.utc)

    # and
    assert len(mail.outbox) == 1


@mock.patch("organisations.chargebee.webhook_handlers.extract_subscription_metadata")
def test_when_cancelled_subscription_is_renewed_then_subscription_activated_and_no_cancellation_email_sent(
    mock_extract_subscription_metadata: MagicMock,
    subscription: Subscription,
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    subscription.cancellation_date = datetime.now(tz=UTC) - timedelta(days=1)
    subscription.subscription_id = "subscription-id"
    subscription.save()
    mail.outbox.clear()

    mock_extract_subscription_metadata.return_value = ChargebeeObjMetadata(
        seats=3,
        api_calls=100,
        projects=1,
        chargebee_email=staff_user.email,
    )
    data = {
        "content": {
            "subscription": {
                "status": "active",
                "id": subscription.subscription_id,
            },
            "customer": {"email": staff_user.email},
        }
    }
    url = reverse("api-v1:chargebee-webhook")
    # When
    staff_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    subscription.refresh_from_db()
    assert subscription.cancellation_date is None

    # and
    assert not mail.outbox


def test_when_chargebee_webhook_received_with_unknown_subscription_id_then_200(
    api_client: APIClient, caplog: LogCaptureFixture, django_user_model: Type[Model]
) -> None:
    # Given
    subscription_id = "some-random-id"
    cb_user = django_user_model.objects.create(email="test@example.com", is_staff=True)
    api_client.force_authenticate(cb_user)

    data = {
        "content": {
            "subscription": {"status": "active", "id": subscription_id},
            "customer": {"email": cb_user.email},
        }
    }
    url = reverse("api-v1:chargebee-webhook")

    # When
    res = api_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_200_OK

    assert len(caplog.records) == 1
    assert caplog.record_tuples[0] == (
        "organisations.chargebee.webhook_handlers",
        30,
        f"Couldn't get unique subscription for ChargeBee id {subscription_id}",
    )


def test_user_can_create_new_webhook(
    admin_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    valid_webhook_url = "http://my.webhook.com/webhooks"
    data = {"url": valid_webhook_url}
    url = reverse(
        "api-v1:organisations:organisation-webhooks-list",
        args=[organisation.id],
    )
    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_can_update_secret_for_webhook(
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    valid_webhook_url = "http://my.webhook.com/webhooks"
    webhook = OrganisationWebhook.objects.create(
        url=valid_webhook_url, organisation=organisation
    )
    url = reverse(
        "api-v1:organisations:organisation-webhooks-detail",
        args=[organisation.id, webhook.id],
    )
    data = {"secret": "random_key"}

    # When
    res = admin_client.patch(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["secret"] == data["secret"]

    # and
    webhook.refresh_from_db()
    assert webhook.secret == data["secret"]


@mock.patch("webhooks.mixins.trigger_sample_webhook")
def test_trigger_sample_webhook_calls_trigger_sample_webhook_method_with_correct_arguments(
    trigger_sample_webhook: MagicMock,
    organisation: Organisation,
    admin_client: APIClient,
) -> None:
    # Given
    mocked_response = mock.MagicMock(status_code=200)
    trigger_sample_webhook.return_value = mocked_response

    url = reverse(
        "api-v1:organisations:organisation-webhooks-trigger-sample-webhook",
        args=[organisation.id],
    )
    valid_webhook_url = "http://my.webhook.com/webhooks"
    data = {"url": valid_webhook_url}

    # When
    response = admin_client.post(url, data)

    # Then
    assert response.json()["message"] == "Request returned 200"
    assert response.status_code == status.HTTP_200_OK
    args, _ = trigger_sample_webhook.call_args
    assert args[0].url == valid_webhook_url


def test_get_subscription_metadata_when_subscription_information_cache_exist(
    organisation: Organisation,
    admin_client: APIClient,
    chargebee_subscription: Subscription,
    mocker: MagicMock,
) -> None:
    # Given
    expected_seats = 10
    expected_projects = 3
    expected_api_calls = 100
    expected_chargebee_email = "test@example.com"

    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=expected_seats,
        allowed_projects=expected_projects,
        allowed_30d_api_calls=expected_api_calls,
        chargebee_email=expected_chargebee_email,
    )

    url = reverse(
        "api-v1:organisations:organisation-get-subscription-metadata",
        args=[organisation.pk],
    )

    mocker.patch("organisations.models.is_saas", return_value=True)

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "max_seats": expected_seats,
        "max_projects": expected_projects,
        "max_api_calls": expected_api_calls,
        "payment_source": CHARGEBEE,
        "chargebee_email": expected_chargebee_email,
    }


def test_get_subscription_metadata_when_subscription_information_cache_does_not_exist(
    mocker: MockerFixture,
    organisation: Organisation,
    admin_client: APIClient,
    chargebee_subscription: Subscription,
) -> None:
    # Given
    expected_seats = 10
    expected_projects = 5
    expected_api_calls = 100
    expected_chargebee_email = "test@example.com"

    mocker.patch("organisations.models.is_saas", return_value=True)
    get_subscription_metadata = mocker.patch(
        "organisations.models.get_subscription_metadata_from_id",
        return_value=ChargebeeObjMetadata(
            seats=expected_seats,
            projects=expected_projects,
            api_calls=expected_api_calls,
            chargebee_email=expected_chargebee_email,
        ),
    )

    url = reverse(
        "api-v1:organisations:organisation-get-subscription-metadata",
        args=[organisation.pk],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "max_seats": expected_seats,
        "max_projects": expected_projects,
        "max_api_calls": expected_api_calls,
        "payment_source": CHARGEBEE,
        "chargebee_email": expected_chargebee_email,
    }
    get_subscription_metadata.assert_called_once_with(
        chargebee_subscription.subscription_id
    )


def test_get_subscription_metadata_returns_200_if_the_organisation_have_no_paid_subscription(
    mocker: MockerFixture, organisation: Organisation, admin_client: APIClient
) -> None:
    # Given
    get_subscription_metadata = mocker.patch(
        "organisations.models.get_subscription_metadata_from_id"
    )
    assert organisation.subscription.subscription_id is None
    url = reverse(
        "api-v1:organisations:organisation-get-subscription-metadata",
        args=[organisation.pk],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "chargebee_email": None,
        "max_api_calls": 50000,
        # MAX_PROJECTS_IN_FREE_PLAN is set to 10 in tests, as there are tests that needs to create more
        # than 1 project within a single organisation using the default subscription
        "max_projects": settings.MAX_PROJECTS_IN_FREE_PLAN,
        "max_seats": 1,
        "payment_source": None,
    }

    get_subscription_metadata.assert_not_called()


def test_get_subscription_metadata_returns_defaults_if_chargebee_error(
    organisation, admin_client, chargebee_subscription
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-get-subscription-metadata",
        args=[organisation.pk],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "max_seats": MAX_SEATS_IN_FREE_PLAN,
        "max_api_calls": MAX_API_CALLS_IN_FREE_PLAN,
        "max_projects": settings.MAX_PROJECTS_IN_FREE_PLAN,
        "payment_source": None,
        "chargebee_email": None,
    }


def test_can_invite_user_with_permission_groups(
    settings, admin_client, organisation, user_permission_group
) -> None:
    # Given
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None

    url = reverse("api-v1:organisations:organisation-invite", args=[organisation.pk])
    invited_email = "test@example.com"

    data = {
        "invites": [
            {
                "email": invited_email,
                "role": OrganisationRole.ADMIN.name,
                "permission_groups": [user_permission_group.id],
            }
        ]
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()[0]["permission_groups"] == [user_permission_group.id]

    # and
    invite = Invite.objects.get(email=invited_email)
    assert user_permission_group in invite.permission_groups.all()


@pytest.mark.parametrize(
    "query_string, expected_filter_args",
    (
        ("", {}),
        ("project_id=1", {"project_id": 1}),
        ("project_id=1&environment_id=1", {"project_id": 1, "environment_id": 1}),
        ("environment_id=1", {"environment_id": 1}),
    ),
)
def test_organisation_get_influx_data(
    mocker, admin_client, organisation, query_string, expected_filter_args
) -> None:
    # Given
    base_url = reverse(
        "api-v1:organisations:organisation-get-influx-data", args=[organisation.id]
    )
    url = f"{base_url}?{query_string}"
    mock_get_multiple_event_list_for_organisation = mocker.patch(
        "organisations.views.get_multiple_event_list_for_organisation"
    )
    mock_get_multiple_event_list_for_organisation.return_value = []

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    mock_get_multiple_event_list_for_organisation.assert_called_once_with(
        str(organisation.id), **expected_filter_args
    )
    assert response.json() == {"events_list": []}


@freeze_time("2023-07-31 12:00:00")
@pytest.mark.parametrize(
    "plan_id, max_seats, max_api_calls, max_projects, is_updated",
    [
        ("plan-id", 3, 100, 3, False),
        ("updated-plan-id", 5, 500, 10, True),
    ],
)
@mock.patch("organisations.models.get_plan_meta_data")
@mock.patch("organisations.chargebee.webhook_handlers.extract_subscription_metadata")
def test_when_plan_is_changed_max_seats_and_max_api_calls_are_updated(
    mock_extract_subscription_metadata,
    mock_get_plan_meta_data,
    subscription,
    admin_client,
    organisation,
    plan_id,
    max_seats,
    max_api_calls,
    max_projects,
    is_updated,
) -> None:
    # Given
    chargebee_email = "chargebee@test.com"
    url = reverse("api-v1:chargebee-webhook")
    updated_at = datetime.now(tz=UTC) - timedelta(
        days=1
    )  # The timestamp representing the last update time, one day ago from the current time.

    mock_get_plan_meta_data.return_value = {
        "seats": max_seats,
        "api_calls": max_api_calls,
    }
    mock_extract_subscription_metadata.return_value = ChargebeeObjMetadata(
        seats=max_seats,
        api_calls=max_api_calls,
        projects=max_projects,
        chargebee_email=chargebee_email,
    )
    subscription.subscription_id = "sub-id"
    subscription.save()

    data = {
        "content": {
            "subscription": {
                "status": "active",
                "id": subscription.subscription_id,
                "plan_id": plan_id,
            },
            "customer": {"email": chargebee_email},
        }
    }

    if is_updated:
        subscription_information_cache = (
            OrganisationSubscriptionInformationCache.objects.create(
                organisation=organisation,
                allowed_seats=1,
                allowed_30d_api_calls=10,
                allowed_projects=1,
                chargebee_email=chargebee_email,
                chargebee_updated_at=updated_at,
                influx_updated_at=None,
            )
        )

    # When
    res = admin_client.post(url, data=json.dumps(data), content_type="application/json")

    subscription_information_cache = (
        OrganisationSubscriptionInformationCache.objects.get(organisation=organisation)
    )

    subscription.refresh_from_db()
    # Then
    assert res.status_code == status.HTTP_200_OK
    assert subscription.plan == plan_id
    assert subscription.max_seats == max_seats
    assert subscription.max_api_calls == max_api_calls

    assert subscription_information_cache.allowed_seats == max_seats
    assert subscription_information_cache.allowed_30d_api_calls == max_api_calls
    assert subscription_information_cache.allowed_projects == max_projects
    assert subscription_information_cache.chargebee_email == chargebee_email
    assert subscription_information_cache.chargebee_updated_at
    assert subscription_information_cache.influx_updated_at is None
    if is_updated:
        assert subscription_information_cache.chargebee_updated_at > updated_at


def test_delete_organisation_does_not_delete_all_subscriptions_from_the_database(
    admin_client, admin_user, organisation, subscription
) -> None:
    """
    Test to verify workaround for bug in django-softdelete as per issue here:
    https://github.com/scoursen/django-softdelete/issues/99
    """

    # Given
    # another organisation
    another_organisation = Organisation.objects.create(name="another org")
    admin_user.add_organisation(another_organisation)

    url = reverse("api-v1:organisations:organisation-detail", args=[organisation.id])

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert Subscription.objects.filter(organisation=another_organisation).exists()


def test_make_user_group_admin_user_does_not_belong_to_group(
    admin_client, admin_user, organisation, user_permission_group
) -> None:
    # Given
    another_user = FFAdminUser.objects.create(email="another_user@example.com")
    another_user.add_organisation(organisation)
    url = reverse(
        "api-v1:organisations:make-user-group-admin",
        args=[organisation.id, user_permission_group.id, another_user.id],
    )

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_make_user_group_admin_success(
    admin_client, admin_user, organisation, user_permission_group
) -> None:
    # Given
    another_user = FFAdminUser.objects.create(email="another_user@example.com")
    another_user.add_organisation(organisation)
    another_user.permission_groups.add(user_permission_group)
    url = reverse(
        "api-v1:organisations:make-user-group-admin",
        args=[organisation.id, user_permission_group.id, another_user.id],
    )

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        UserPermissionGroupMembership.objects.get(
            ffadminuser=another_user,
            userpermissiongroup=user_permission_group,
        ).group_admin
        is True
    )


def test_make_user_group_admin_forbidden(
    staff_client: APIClient,
    organisation: Organisation,
    user_permission_group: UserPermissionGroup,
) -> None:
    # Given
    another_user = FFAdminUser.objects.create(email="another_user@example.com")
    another_user.add_organisation(organisation)
    another_user.permission_groups.add(user_permission_group)
    url = reverse(
        "api-v1:organisations:make-user-group-admin",
        args=[organisation.id, user_permission_group.id, another_user.id],
    )

    # When
    response = staff_client.post(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_remove_user_as_group_admin_user_does_not_belong_to_group(
    admin_client, admin_user, organisation, user_permission_group
) -> None:
    # Given
    another_user = FFAdminUser.objects.create(email="another_user@example.com")
    another_user.add_organisation(organisation)
    url = reverse(
        "api-v1:organisations:remove-user-group-admin",
        args=[organisation.id, user_permission_group.id, another_user.id],
    )

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_remove_user_as_group_admin_success(
    admin_client, admin_user, organisation, user_permission_group
) -> None:
    # Given
    another_user = FFAdminUser.objects.create(email="another_user@example.com")
    another_user.add_organisation(organisation)
    another_user.permission_groups.add(user_permission_group)
    another_user.make_group_admin(user_permission_group.id)
    url = reverse(
        "api-v1:organisations:remove-user-group-admin",
        args=[organisation.id, user_permission_group.id, another_user.id],
    )

    # When
    response = admin_client.post(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        UserPermissionGroupMembership.objects.get(
            ffadminuser=another_user,
            userpermissiongroup=user_permission_group,
        ).group_admin
        is False
    )


def test_remove_user_as_group_admin_forbidden(
    staff_client: APIClient,
    organisation: Organisation,
    user_permission_group: UserPermissionGroup,
) -> None:
    # Given
    another_user = FFAdminUser.objects.create(email="another_user@example.com")
    another_user.add_organisation(organisation)
    another_user.permission_groups.add(user_permission_group)
    another_user.make_group_admin(user_permission_group.id)
    url = reverse(
        "api-v1:organisations:remove-user-group-admin",
        args=[organisation.id, user_permission_group.id, another_user.id],
    )

    # When
    response = staff_client.post(url)
    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_user_groups_as_group_admin(organisation, api_client) -> None:
    # Given
    user1 = FFAdminUser.objects.create(email="user1@example.com")
    user2 = FFAdminUser.objects.create(email="user2@example.com")

    user1.add_organisation(organisation)
    user2.add_organisation(organisation)

    user_permission_group_1 = UserPermissionGroup.objects.create(
        organisation=organisation, name="group1"
    )
    user_permission_group_2 = UserPermissionGroup.objects.create(
        organisation=organisation, name="group2"
    )

    UserPermissionGroupMembership.objects.create(
        ffadminuser=user1, userpermissiongroup=user_permission_group_1, group_admin=True
    )
    UserPermissionGroupMembership.objects.create(
        ffadminuser=user2, userpermissiongroup=user_permission_group_2, group_admin=True
    )
    UserPermissionGroupMembership.objects.create(
        ffadminuser=user1, userpermissiongroup=user_permission_group_2
    )

    api_client.force_authenticate(user1)
    url = reverse(
        "api-v1:organisations:organisation-groups-list", args=[organisation.id]
    )

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["id"] == user_permission_group_1.id


def test_list_my_groups(organisation, api_client) -> None:
    # Given
    user1 = FFAdminUser.objects.create(email="user1@example.com")
    user2 = FFAdminUser.objects.create(email="user2@example.com")

    user1.add_organisation(organisation)
    user2.add_organisation(organisation)

    # Group 1 with user 1 in it only
    user_permission_group_1 = UserPermissionGroup.objects.create(
        organisation=organisation, name="group1"
    )
    UserPermissionGroupMembership.objects.create(
        ffadminuser=user1, userpermissiongroup=user_permission_group_1
    )

    # Group 2 with user 2 in it only
    user_permission_group_2 = UserPermissionGroup.objects.create(
        organisation=organisation, name="group2"
    )
    UserPermissionGroupMembership.objects.create(
        ffadminuser=user2, userpermissiongroup=user_permission_group_2
    )

    api_client.force_authenticate(user1)
    url = reverse(
        "api-v1:organisations:organisation-groups-my-groups", args=[organisation.id]
    )

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0] == {
        "id": user_permission_group_1.id,
        "name": user_permission_group_1.name,
    }


def test_payment_failed_chargebee_webhook(
    staff_client: FFAdminUser, subscription: Subscription
) -> None:
    # Given
    subscription.billing_status = SUBSCRIPTION_BILLING_STATUS_ACTIVE
    subscription.subscription_id = "best_id"
    subscription.save()

    data = {
        "id": "someId",
        "occurred_at": 1699630568,
        "object": "event",
        "api_version": "v2",
        "content": {
            "invoice": {
                "subscription_id": subscription.subscription_id,
                "dunning_status": "in_progress",
            },
        },
        "event_type": "payment_failed",
    }

    url = reverse("api-v1:chargebee-webhook")

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 200
    subscription.refresh_from_db()
    assert subscription.billing_status == SUBSCRIPTION_BILLING_STATUS_DUNNING


def test_payment_failed_chargebee_webhook_when_not_dunning(
    staff_client: FFAdminUser, subscription: Subscription
) -> None:
    # Given
    subscription.billing_status = SUBSCRIPTION_BILLING_STATUS_ACTIVE
    subscription.subscription_id = "best_id"
    subscription.save()

    data = {
        "id": "someId",
        "occurred_at": 1699630568,
        "object": "event",
        "api_version": "v2",
        "content": {
            "invoice": {
                "subscription_id": subscription.subscription_id,
                "dunning_status": "inactive",  # Key field
            },
        },
        "event_type": "payment_failed",
    }

    url = reverse("api-v1:chargebee-webhook")

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 200
    subscription.refresh_from_db()

    # Since the dunning inactive keep subscription active
    assert subscription.billing_status == SUBSCRIPTION_BILLING_STATUS_ACTIVE


def test_when_subscription_is_cancelled_then_remove_all_but_the_first_user(
    staff_client: APIClient,
    subscription: Subscription,
    organisation: Organisation,
) -> None:
    # Given
    cancellation_date = datetime.now(tz=UTC)
    current_term_end = int(datetime.timestamp(cancellation_date))
    subscription.subscription_id = "subscription_id23"
    subscription.save()

    data = {
        "content": {
            "subscription": {
                "status": "cancelled",
                "id": subscription.subscription_id,
                "current_term_end": current_term_end,
            },
            "customer": {
                "email": "chargebee@bullet-train.io",
            },
        }
    }

    url = reverse("api-v1:chargebee-webhook")
    assert organisation.num_seats == 2

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 200

    subscription.refresh_from_db()

    # Subscription is now a free plan.
    assert subscription.cancellation_date is None
    organisation.refresh_from_db()
    assert organisation.num_seats == 1


def test_payment_failed_chargebee_webhook_no_subscription_id(
    staff_client: FFAdminUser, subscription: Subscription
) -> None:
    # Given
    subscription.billing_status = SUBSCRIPTION_BILLING_STATUS_ACTIVE
    subscription.subscription_id = "best_id"
    subscription.save()

    data = {
        "id": "someId",
        "occurred_at": 1699630568,
        "object": "event",
        "api_version": "v2",
        "content": {
            "invoice": {  # Missing subscription id
                "dunning_status": "in_progress",
            },
        },
        "event_type": "payment_failed",
    }

    url = reverse("api-v1:chargebee-webhook")

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 200
    subscription.refresh_from_db()
    assert subscription.billing_status == SUBSCRIPTION_BILLING_STATUS_ACTIVE


def test_cache_rebuild_event_chargebee_webhook(
    staff_client: FFAdminUser,
    mocker: MockerFixture,
) -> None:
    # Given
    data = {
        "id": "ev_XpbG6hnQqGFm2n3O",
        "occurred_at": 1341085213,
        "source": "api",
        "user": "full_access_key_v1",
        "object": "event",
        "api_version": "v2",
        "content": {
            "addon": {
                "id": "support",
                "name": "Support",
                "description": "This is addon added when support is needed",
                "type": "quantity",
                "charge_type": "recurring",
                "price": 1000,
                "period": 1,
                "period_unit": "month",
                "status": "deleted",
            }
        },
        "event_type": "addon_deleted",
    }

    url = reverse("api-v1:chargebee-webhook")
    task = mocker.patch(
        "organisations.chargebee.webhook_handlers.update_chargebee_cache"
    )
    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == 200
    task.delay.assert_called_once_with()


def test_payment_succeeded_chargebee_webhook(
    staff_client: FFAdminUser, subscription: Subscription
) -> None:
    # Given
    subscription.billing_status = SUBSCRIPTION_BILLING_STATUS_DUNNING
    subscription.subscription_id = "best_id"
    subscription.save()

    data = {
        "id": "someId",
        "occurred_at": 1699630568,
        "object": "event",
        "api_version": "v2",
        "content": {
            "invoice": {
                "subscription_id": subscription.subscription_id,
            },
        },
        "event_type": "payment_succeeded",
    }

    url = reverse("api-v1:chargebee-webhook")

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 200
    subscription.refresh_from_db()
    assert subscription.billing_status == SUBSCRIPTION_BILLING_STATUS_ACTIVE


def test_payment_succeeded_chargebee_webhook_no_subscription_id(
    staff_client: FFAdminUser, subscription: Subscription
) -> None:
    # Given
    subscription.billing_status = SUBSCRIPTION_BILLING_STATUS_DUNNING
    subscription.subscription_id = "best_id"
    subscription.save()

    data = {
        "id": "someId",
        "occurred_at": 1699630568,
        "object": "event",
        "api_version": "v2",
        "content": {
            "invoice": {"not_subscription_id": "irrelevant data"},
        },
        "event_type": "payment_succeeded",
    }

    url = reverse("api-v1:chargebee-webhook")

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 200
    subscription.refresh_from_db()
    assert subscription.billing_status == SUBSCRIPTION_BILLING_STATUS_DUNNING


def test_list_organisations_shows_dunning(
    staff_client: FFAdminUser, subscription: Subscription
) -> None:
    # Given
    subscription.billing_status = SUBSCRIPTION_BILLING_STATUS_DUNNING
    subscription.save()
    url = reverse("api-v1:organisations:organisation-list")

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    _subscription = response.data["results"][0]["subscription"]
    assert _subscription["id"] == subscription.id
    assert _subscription["billing_status"] == SUBSCRIPTION_BILLING_STATUS_DUNNING


def test_list_group_summaries(
    organisation: Organisation, staff_client: APIClient
) -> None:
    # Given
    user_permission_group_1 = UserPermissionGroup.objects.create(
        organisation=organisation, name="group1"
    )
    user_permission_group_2 = UserPermissionGroup.objects.create(
        organisation=organisation, name="group2"
    )

    url = reverse(
        "api-v1:organisations:organisation-groups-summaries", args=[organisation.id]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2
    assert response_json[0] == {
        "id": user_permission_group_1.id,
        "name": user_permission_group_1.name,
    }
    assert response_json[1] == {
        "id": user_permission_group_2.id,
        "name": user_permission_group_2.name,
    }


def test_user_from_another_organisation_cannot_list_group_summaries(
    organisation: Organisation, api_client: APIClient
) -> None:
    # Given
    UserPermissionGroup.objects.create(organisation=organisation, name="group1")

    organisation_2 = Organisation.objects.create(name="org2")
    org2_user = FFAdminUser.objects.create(email="org2user@example.com")
    org2_user.add_organisation(organisation_2)
    api_client.force_authenticate(org2_user)

    url = reverse(
        "api-v1:organisations:organisation-groups-summaries", args=[organisation.id]
    )

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_defaults_to_empty_api_notifications_when_no_subscription_information_cache(
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-api-usage-notification",
        args=[organisation.id],
    )

    now = timezone.now()
    OranisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=90,
        notified_at=now,
    )

    assert hasattr(organisation, "subscription_information_cache") is False

    # When
    response = staff_client.get(url)

    # Then
    # There are no results even if there is a notification because
    # the information cache can't provide an estimate as to API usage.
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"] == []


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_retrieves_api_usage_notifications(
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-api-usage-notification",
        args=[organisation.id],
    )

    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=45),
        current_billing_term_ends_at=now + timedelta(days=320),
    )

    # Add three notifications, but we only get the 100% one.
    OranisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=90,
        notified_at=now,
    )
    OranisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=75,
        notified_at=now,
    )
    OranisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["notified_at"] == "2023-01-19T09:09:47.325132Z"
    assert response.data["results"][0]["organisation_id"] == organisation.id
    assert response.data["results"][0]["percent_usage"] == 100


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_doesnt_retrieve_stale_api_usage_notifications(
    staff_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-api-usage-notification",
        args=[organisation.id],
    )

    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=45),
        current_billing_term_ends_at=now + timedelta(days=320),
    )

    # Create a notification in the past which should not be shown.
    OranisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=90,
        notified_at=now - timedelta(20),
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 0


def test_non_organisation_user_cannot_remove_user_from_organisation(
    staff_user: FFAdminUser, organisation: Organisation, api_client: APIClient
) -> None:
    # Given
    another_organisation = Organisation.objects.create(name="another organisation")
    another_user = FFAdminUser.objects.create(email="another_user@example.com")
    another_user.add_organisation(another_organisation)
    api_client.force_authenticate(another_user)

    url = reverse(
        "api-v1:organisations:organisation-remove-users", args=[organisation.id]
    )

    data = [{"id": staff_user.id}]

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_non_admin_user_cannot_remove_user_from_organisation(
    staff_user: FFAdminUser,
    organisation: Organisation,
    staff_client: APIClient,
    admin_user: FFAdminUser,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-remove-users", args=[organisation.id]
    )

    data = [{"id": admin_user.id}]

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_validation_error_if_non_numeric_organisation_id(
    staff_client: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:organisations:organisation-remove-users", args=["foo"])

    data = []

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

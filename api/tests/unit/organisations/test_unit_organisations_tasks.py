import uuid
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from django.core.mail.message import EmailMultiAlternatives
from django.utils import timezone
from pytest_mock import MockerFixture

from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.models import (
    OranisationAPIUsageNotification,
    Organisation,
    OrganisationRole,
    OrganisationSubscriptionInformationCache,
    UserOrganisation,
)
from organisations.subscriptions.constants import (
    FREE_PLAN_ID,
    MAX_API_CALLS_IN_FREE_PLAN,
    MAX_SEATS_IN_FREE_PLAN,
)
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata
from organisations.tasks import (
    ALERT_EMAIL_MESSAGE,
    ALERT_EMAIL_SUBJECT,
    finish_subscription_cancellation,
    handle_api_usage_notifications,
    send_org_over_limit_alert,
    send_org_subscription_cancelled_alert,
)
from users.models import FFAdminUser


def test_send_org_over_limit_alert_for_organisation_with_free_subscription(
    organisation, mocker
):
    # Given
    mocked_ffadmin_user = mocker.patch("organisations.tasks.FFAdminUser")

    # When
    send_org_over_limit_alert(organisation.id)

    # Then
    args, kwargs = mocked_ffadmin_user.send_alert_to_admin_users.call_args
    assert len(args) == 0
    assert len(kwargs) == 2
    assert kwargs["message"] == ALERT_EMAIL_MESSAGE % (
        organisation.name,
        organisation.num_seats,
        MAX_SEATS_IN_FREE_PLAN,
        FREE_PLAN_ID,
    )
    assert kwargs["subject"] == ALERT_EMAIL_SUBJECT


@pytest.mark.parametrize(
    "SubscriptionMetadata", [ChargebeeObjMetadata, XeroSubscriptionMetadata]
)
def test_send_org_over_limit_alert_for_organisation_with_subscription(
    organisation, subscription, mocker, SubscriptionMetadata
):
    # Given
    mocked_ffadmin_user = mocker.patch("organisations.tasks.FFAdminUser")
    max_seats = 10
    mocker.patch(
        "organisations.tasks.get_subscription_metadata",
        return_value=SubscriptionMetadata(seats=max_seats),
    )

    # When
    send_org_over_limit_alert(organisation.id)

    # Then
    args, kwargs = mocked_ffadmin_user.send_alert_to_admin_users.call_args
    assert len(args) == 0
    assert len(kwargs) == 2
    assert kwargs["message"] == ALERT_EMAIL_MESSAGE % (
        organisation.name,
        organisation.num_seats,
        max_seats,
        subscription.plan,
    )
    assert kwargs["subject"] == ALERT_EMAIL_SUBJECT


def test_subscription_cancellation(db: None) -> None:
    # Given
    organisation = Organisation.objects.create()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
    )
    UserOrganisation.objects.create(
        organisation=organisation,
        user=FFAdminUser.objects.create(email=f"{uuid.uuid4()}@example.com"),
        role=OrganisationRole.ADMIN,
    )

    assert organisation.subscription_information_cache
    subscription = organisation.subscription
    notes = "Notes to be kept"
    subscription.subscription_id = "id"
    subscription.subscription_date = timezone.now()
    subscription.plan = "plan_code"
    subscription.max_seats = 1_000_000
    subscription.max_api_calls = 1_000_000
    subscription.cancellation_date = timezone.now()
    subscription.customer_id = "customer23"
    subscription.billing_status = "ACTIVE"
    subscription.payment_method = "CHARGEBEE"
    subscription.notes = notes

    subscription.save()

    # When
    finish_subscription_cancellation()

    # Then
    organisation.refresh_from_db()
    subscription.refresh_from_db()
    assert getattr(organisation, "subscription_information_cache", None) is None
    assert subscription.subscription_id is None
    assert subscription.subscription_date is None
    assert subscription.plan == FREE_PLAN_ID
    assert subscription.max_seats == MAX_SEATS_IN_FREE_PLAN
    assert subscription.max_api_calls == MAX_API_CALLS_IN_FREE_PLAN
    assert subscription.cancellation_date is None
    assert subscription.customer_id is None
    assert subscription.billing_status is None
    assert subscription.payment_method is None
    assert subscription.cancellation_date is None
    assert subscription.notes == notes


@pytest.mark.freeze_time("2023-01-19T09:12:34+00:00")
def test_finish_subscription_cancellation(db: None, mocker: MockerFixture) -> None:
    # Given
    send_org_subscription_cancelled_alert_task = mocker.patch(
        "organisations.tasks.send_org_subscription_cancelled_alert"
    )

    organisation1 = Organisation.objects.create(name="TestCorp")
    organisation2 = Organisation.objects.create()
    organisation3 = Organisation.objects.create()
    organisation4 = Organisation.objects.create()

    # Far future cancellation will be unaffected.
    organisation_user_count = 3
    for __ in range(organisation_user_count):
        UserOrganisation.objects.create(
            organisation=organisation1,
            user=FFAdminUser.objects.create(email=f"{uuid.uuid4()}@example.com"),
            role=OrganisationRole.ADMIN,
        )
    future = timezone.now() + timedelta(days=20)
    organisation1.subscription.prepare_for_cancel(cancellation_date=future)

    # Test one of the send org alerts.
    send_org_subscription_cancelled_alert_task.delay.assert_called_once_with(
        kwargs={
            "organisation_name": organisation1.name,
            "formatted_cancellation_date": "2023-02-08 09:12:34",
        }
    )

    # Two organisations are impacted.
    for __ in range(organisation_user_count):
        UserOrganisation.objects.create(
            organisation=organisation2,
            user=FFAdminUser.objects.create(email=f"{uuid.uuid4()}@example.com"),
            role=OrganisationRole.ADMIN,
        )

    organisation2.subscription.prepare_for_cancel(
        cancellation_date=timezone.now() - timedelta(hours=2)
    )

    for __ in range(organisation_user_count):
        UserOrganisation.objects.create(
            organisation=organisation3,
            user=FFAdminUser.objects.create(email=f"{uuid.uuid4()}@example.com"),
            role=OrganisationRole.ADMIN,
        )
    organisation3.subscription.prepare_for_cancel(
        cancellation_date=timezone.now() - timedelta(hours=4)
    )

    # Remaining organisation4 has not canceled, should be left unaffected.
    for __ in range(organisation_user_count):
        UserOrganisation.objects.create(
            organisation=organisation4,
            user=FFAdminUser.objects.create(email=f"{uuid.uuid4()}@example.com"),
            role=OrganisationRole.ADMIN,
        )

    # When
    finish_subscription_cancellation()

    # Then
    organisation1.refresh_from_db()
    organisation2.refresh_from_db()
    organisation3.refresh_from_db()
    organisation4.refresh_from_db()

    assert organisation1.num_seats == organisation_user_count
    assert organisation2.num_seats == 1
    assert organisation3.num_seats == 1
    assert organisation4.num_seats == organisation_user_count


def test_send_org_subscription_cancelled_alert(db: None, mocker: MockerFixture) -> None:
    # Given
    send_mail_mock = mocker.patch("users.models.send_mail")

    # When
    send_org_subscription_cancelled_alert(
        organisation_name="TestCorp",
        formatted_cancellation_date="2023-02-08 09:12:34",
    )

    # Then
    send_mail_mock.assert_called_once_with(
        subject="Organisation TestCorp has cancelled their subscription",
        message="Organisation TestCorp has cancelled their subscription on 2023-02-08 09:12:34",
        from_email="noreply@flagsmith.com",
        recipient_list=[],
        fail_silently=True,
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications_when_feature_flag_is_off(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
) -> None:
    # Given
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
    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = False

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_not_called()

    assert len(mailoutbox) == 0
    assert (
        OranisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 0
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications_below_100(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
) -> None:
    # Given
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
    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 91
    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    assert not OranisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_called_once_with(organisation.id, "14d")

    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == "Flagsmith API use has reached 90%"
    assert email.body == (
        "Hi there,\n\nThe API usage for Test Org has reached "
        "90% within the current subscription period. Please "
        "consider upgrading your organisations account limits.\n\n"
        "Thank you!\n\nThe Flagsmith Team\n"
    )

    assert len(email.alternatives) == 1
    assert len(email.alternatives[0]) == 2
    assert email.alternatives[0][1] == "text/html"

    assert email.alternatives[0][0] == (
        "<table>\n\n        <tr>\n\n               "
        "<td>Hi there,</td>\n\n        </tr>\n\n        "
        "<tr>\n\n               <td>\n                 "
        "The API usage for Test Org has reached\n                 "
        "90% within the current subscription period.\n                 "
        "Please consider upgrading your organisations account limits.\n"
        "               </td>\n\n\n        </tr>\n\n        "
        "<tr>\n\n               <td>Thank you!</td>\n\n      "
        "  </tr>\n\n        <tr>\n\n               "
        "<td>The Flagsmith Team</td>\n\n        "
        "</tr>\n\n</table>\n"
    )

    assert email.from_email == "noreply@flagsmith.com"
    # Only admin because threshold is under 100.
    assert email.to == ["admin@example.com"]

    assert (
        OranisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )
    api_usage_notification = OranisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).first()

    assert api_usage_notification.percent_usage == 90

    # Now re-run the usage to make sure the notification isn't resent.
    handle_api_usage_notifications()

    assert (
        OranisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )
    assert OranisationAPIUsageNotification.objects.first() == api_usage_notification


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications_above_100(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
) -> None:
    # Given
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
    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 105

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    assert not OranisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_called_once_with(organisation.id, "14d")

    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == "Flagsmith API use has reached 100%"
    assert email.body == (
        "Hi there,\n\nThe API usage for Test Org has breached "
        "100% within the current subscription period. Please "
        "upgrade your organisations account to ensure "
        "continued service.\n\nThank you!\n\n"
        "The Flagsmith Team\n"
    )

    assert len(email.alternatives) == 1
    assert len(email.alternatives[0]) == 2
    assert email.alternatives[0][1] == "text/html"

    assert email.alternatives[0][0] == (
        "<table>\n\n        <tr>\n\n               <td>Hi "
        "there,</td>\n\n        </tr>\n\n        <tr>\n\n    "
        "           <td>\n                 The API usage for Test Org "
        "has breached\n                 100% within the "
        "current subscription period.\n                 "
        "Please upgrade your organisations account to ensure "
        "continued service.\n               </td>\n\n\n      "
        "  </tr>\n\n        <tr>\n\n               <td>"
        "Thank you!</td>\n\n        </tr>\n\n        <tr>\n\n"
        "               <td>The Flagsmith Team</td>\n\n        "
        "</tr>\n\n</table>\n"
    )

    assert email.from_email == "noreply@flagsmith.com"
    # Extra staff included because threshold is over 100.
    assert email.to == ["admin@example.com", "staff@example.com"]

    assert (
        OranisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )
    api_usage_notification = OranisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).first()

    assert api_usage_notification.percent_usage == 100

    # Now re-run the usage to make sure the notification isn't resent.
    handle_api_usage_notifications()

    assert (
        OranisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )
    assert OranisationAPIUsageNotification.objects.first() == api_usage_notification

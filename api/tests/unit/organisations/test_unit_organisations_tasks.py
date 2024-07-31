import logging
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, call

import pytest
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from freezegun.api import FrozenDateTimeFactory
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.constants import (
    API_USAGE_ALERT_THRESHOLDS,
    API_USAGE_GRACE_PERIOD,
)
from organisations.models import (
    APILimitAccessBlock,
    Organisation,
    OrganisationAPIBilling,
    OrganisationAPIUsageNotification,
    OrganisationRole,
    OrganisationSubscriptionInformationCache,
    UserOrganisation,
)
from organisations.subscriptions.constants import (
    CHARGEBEE,
    FREE_PLAN_ID,
    MAX_API_CALLS_IN_FREE_PLAN,
    MAX_SEATS_IN_FREE_PLAN,
    SCALE_UP,
)
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata
from organisations.tasks import (
    ALERT_EMAIL_MESSAGE,
    ALERT_EMAIL_SUBJECT,
    charge_for_api_call_count_overages,
    finish_subscription_cancellation,
    handle_api_usage_notifications,
    register_recurring_tasks,
    restrict_use_due_to_api_limit_grace_period_over,
    send_org_over_limit_alert,
    send_org_subscription_cancelled_alert,
    unrestrict_after_api_limit_grace_period_is_stale,
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

    client_mock.get_identity_flags.assert_called_once_with(
        organisation.flagsmith_identifier,
        traits={
            "organisation_id": organisation.id,
            "subscription.plan": organisation.subscription.plan,
        },
    )

    assert len(mailoutbox) == 0
    assert (
        OrganisationAPIUsageNotification.objects.filter(
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
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.subscription_id = "fancy_id"
    organisation.subscription.save()
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
        "organisations.task_helpers.get_current_api_usage",
    )
    mock_api_usage.return_value = 91
    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    assert not OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_called_once_with(organisation.id, "-14d")

    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == "Flagsmith API use has reached 90%"
    assert email.body == render_to_string(
        "organisations/api_usage_notification.txt",
        context={"organisation": organisation, "matched_threshold": 90},
    )

    assert len(email.alternatives) == 1
    assert len(email.alternatives[0]) == 2
    assert email.alternatives[0][1] == "text/html"

    assert email.alternatives[0][0] == render_to_string(
        "organisations/api_usage_notification.html",
        context={"organisation": organisation, "matched_threshold": 90},
    )

    assert email.from_email == "noreply@flagsmith.com"
    # Only admin because threshold is under 100.
    assert email.to == ["admin@example.com"]

    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )
    api_usage_notification = OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).first()

    assert api_usage_notification.percent_usage == 90

    # Now re-run the usage to make sure the notification isn't resent.
    handle_api_usage_notifications()

    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )
    assert OrganisationAPIUsageNotification.objects.first() == api_usage_notification


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications_below_api_usage_alert_thresholds(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
) -> None:
    # Given
    now = timezone.now()
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.subscription_id = "fancy_id"
    organisation.subscription.save()
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
        "organisations.task_helpers.get_current_api_usage",
    )
    usage = 21
    assert usage < min(API_USAGE_ALERT_THRESHOLDS)
    mock_api_usage.return_value = usage
    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    assert not OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_called_once_with(organisation.id, "-14d")

    assert len(mailoutbox) == 0

    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 0
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications_above_100(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
) -> None:
    # Given
    now = timezone.now()
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.subscription_id = "fancy_id"
    organisation.subscription.save()
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
        "organisations.task_helpers.get_current_api_usage",
    )
    mock_api_usage.return_value = 105

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    assert not OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_called_once_with(organisation.id, "-14d")

    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == "Flagsmith API use has reached 100%"
    assert email.body == render_to_string(
        "organisations/api_usage_notification_limit.txt",
        context={"organisation": organisation, "matched_threshold": 100},
    )

    assert len(email.alternatives) == 1
    assert len(email.alternatives[0]) == 2
    assert email.alternatives[0][1] == "text/html"

    assert email.alternatives[0][0] == render_to_string(
        "organisations/api_usage_notification_limit.html",
        context={"organisation": organisation, "matched_threshold": 100},
    )

    assert email.from_email == "noreply@flagsmith.com"
    # Extra staff included because threshold is over 100.
    assert email.to == ["admin@example.com", "staff@example.com"]

    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )
    api_usage_notification = OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).first()

    assert api_usage_notification.percent_usage == 100

    # Now re-run the usage to make sure the notification isn't resent.
    handle_api_usage_notifications()

    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )

    assert OrganisationAPIUsageNotification.objects.first() == api_usage_notification


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications_with_error(
    mocker: MockerFixture,
    organisation: Organisation,
    inspecting_handler: logging.Handler,
) -> None:
    # Given
    from organisations.tasks import logger

    logger.addHandler(inspecting_handler)

    now = timezone.now()
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.subscription_id = "fancy_id"
    organisation.subscription.save()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=45),
        current_billing_term_ends_at=now + timedelta(days=320),
    )

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    api_usage_patch = mocker.patch(
        "organisations.tasks.handle_api_usage_notification_for_organisation",
        side_effect=ValueError("An error occurred"),
    )

    # When
    handle_api_usage_notifications()

    # Then
    api_usage_patch.assert_called_once_with(organisation)
    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 0
    )
    assert len(inspecting_handler.messages) == 1
    error_message = inspecting_handler.messages[0].split("\n")[0]

    assert (
        error_message
        == f"Error processing api usage for organisation {organisation.id}"
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications_for_free_accounts(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
) -> None:
    # Given
    assert organisation.is_paid is False
    assert organisation.subscription.is_free_plan is True
    assert organisation.subscription.max_api_calls == MAX_API_CALLS_IN_FREE_PLAN

    mock_api_usage = mocker.patch(
        "organisations.task_helpers.get_current_api_usage",
    )
    mock_api_usage.return_value = MAX_API_CALLS_IN_FREE_PLAN + 5_000

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    assert not OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_called_once_with(organisation.id, "-30d")

    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == "Flagsmith API use has reached 100%"
    assert email.body == render_to_string(
        "organisations/api_usage_notification_limit.txt",
        context={"organisation": organisation, "matched_threshold": 100},
    )

    assert len(email.alternatives) == 1
    assert len(email.alternatives[0]) == 2
    assert email.alternatives[0][1] == "text/html"

    assert email.alternatives[0][0] == render_to_string(
        "organisations/api_usage_notification_limit.html",
        context={"organisation": organisation, "matched_threshold": 100},
    )

    assert email.from_email == "noreply@flagsmith.com"
    # Extra staff included because threshold is over 100.
    assert email.to == ["admin@example.com", "staff@example.com"]

    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )
    api_usage_notification = OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).first()

    assert api_usage_notification.percent_usage == 100

    # Now re-run the usage to make sure the notification isn't resent.
    handle_api_usage_notifications()

    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )

    assert OrganisationAPIUsageNotification.objects.first() == api_usage_notification


def test_handle_api_usage_notifications_missing_info_cache(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
    inspecting_handler: logging.Handler,
) -> None:
    # Given
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.save()

    from organisations.task_helpers import logger

    logger.addHandler(inspecting_handler)

    assert organisation.has_subscription_information_cache() is False

    mock_api_usage = mocker.patch(
        "organisations.task_helpers.get_current_api_usage",
    )

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    assert not OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_not_called()

    assert len(mailoutbox) == 0
    assert not OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    assert inspecting_handler.messages == [
        f"Paid organisation {organisation.id} is missing subscription information cache"
    ]


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages_scale_up(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100_000,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=30),
        current_billing_term_ends_at=now + timedelta(minutes=30),
    )
    organisation.subscription.subscription_id = "fancy_sub_id23"
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    mocker.patch("organisations.chargebee.chargebee.chargebee.Subscription.retrieve")
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee.Subscription.update"
    )

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 212_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()

    # Then
    mock_chargebee_update.assert_called_once_with(
        organisation.subscription.subscription_id,
        {
            "addons": [
                {
                    "id": "additional-api-scale-up-monthly",
                    "quantity": 2,  # 200k API requests.
                }
            ],
            "prorate": False,
            "invoice_immediately": False,
        },
    )

    assert OrganisationAPIBilling.objects.count() == 1
    api_billing = OrganisationAPIBilling.objects.first()
    assert api_billing.organisation == organisation
    assert api_billing.api_overage == 200_000
    assert api_billing.immediate_invoice is False
    assert api_billing.billed_at == now


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages_scale_up_when_flagsmith_client_sets_is_enabled_to_false(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100_000,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=30),
        current_billing_term_ends_at=now + timedelta(minutes=30),
    )
    organisation.subscription.subscription_id = "fancy_sub_id23"
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    mocker.patch("organisations.chargebee.chargebee.chargebee.Subscription.retrieve")
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee.Subscription.update"
    )

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = False

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 212_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()

    # Then
    # No charges are applied to the account.
    client_mock.get_identity_flags.assert_called_once_with(
        organisation.flagsmith_identifier,
        traits={
            "organisation_id": organisation.id,
            "subscription.plan": organisation.subscription.plan,
        },
    )
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages_grace_period(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100_000,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=30),
        current_billing_term_ends_at=now + timedelta(minutes=30),
    )
    organisation.subscription.subscription_id = "fancy_sub_id23"
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee.Subscription.update"
    )
    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    # Set the return value to something less than 200% of base rate
    mock_api_usage.return_value = 115_000
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()

    # Then
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages_with_not_covered_plan(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=10_000,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=30),
        current_billing_term_ends_at=now + timedelta(minutes=30),
    )
    organisation.subscription.subscription_id = "fancy_sub_id23"

    # This plan name is what this test hinges on.
    organisation.subscription.plan = "some-plan-not-covered-by-usage"

    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    mocker.patch("organisations.chargebee.chargebee.chargebee.Subscription.retrieve")
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee.Subscription.update"
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 12_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()

    # Then
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages_under_api_limit(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=10_000,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=30),
        current_billing_term_ends_at=now + timedelta(minutes=30),
    )
    organisation.subscription.subscription_id = "fancy_sub_id23"
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    mocker.patch("organisations.chargebee.chargebee.chargebee.Subscription.retrieve")
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee.Subscription.update"
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 2_000
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()

    # Then
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages_start_up(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100_000,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=30),
        current_billing_term_ends_at=now + timedelta(minutes=30),
    )
    organisation.subscription.subscription_id = "fancy_sub_id23"
    organisation.subscription.plan = "startup-v2"
    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True
    mocker.patch("organisations.chargebee.chargebee.chargebee.Subscription.retrieve")
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee.Subscription.update"
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 202_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()

    # Then
    mock_chargebee_update.assert_called_once_with(
        organisation.subscription.subscription_id,
        {
            "addons": [
                {
                    "id": "additional-api-start-up-monthly",
                    "quantity": 2,  # 200k API requests.
                }
            ],
            "prorate": False,
            "invoice_immediately": False,
        },
    )

    assert OrganisationAPIBilling.objects.count() == 1
    api_billing = OrganisationAPIBilling.objects.first()
    assert api_billing.organisation == organisation
    assert api_billing.api_overage == 200_000
    assert api_billing.immediate_invoice is False
    assert api_billing.billed_at == now

    # Now attempt to rebill the account should fail
    calls_mock = mocker.patch(
        "organisations.tasks.add_100k_api_calls_start_up",
    )
    charge_for_api_call_count_overages()
    assert OrganisationAPIBilling.objects.count() == 1
    calls_mock.assert_not_called()


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages_start_up_with_api_billing(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100_000,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=30),
        current_billing_term_ends_at=now + timedelta(minutes=30),
    )
    organisation.subscription.subscription_id = "fancy_sub_id23"
    organisation.subscription.plan = "startup-v2"
    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    OrganisationAPIBilling.objects.create(
        organisation=organisation,
        api_overage=100_000,
        immediate_invoice=False,
        billed_at=now,
    )

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True
    mocker.patch("organisations.chargebee.chargebee.chargebee.Subscription.retrieve")
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee.Subscription.update"
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 202_005
    assert OrganisationAPIBilling.objects.count() == 1

    # When
    charge_for_api_call_count_overages()

    # Then
    mock_chargebee_update.assert_called_once_with(
        organisation.subscription.subscription_id,
        {
            "addons": [
                {
                    "id": "additional-api-start-up-monthly",
                    "quantity": 1,  # 100k API requests.
                }
            ],
            "prorate": False,
            "invoice_immediately": False,
        },
    )

    assert OrganisationAPIBilling.objects.count() == 2


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages_with_yearly_account(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=10_000,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=365),
        current_billing_term_ends_at=now + timedelta(hours=6),
    )
    organisation.subscription.subscription_id = "fancy_sub_id23"
    organisation.subscription.plan = "startup-v2"
    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    mocker.patch("organisations.chargebee.chargebee.chargebee.Subscription.retrieve")
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee.Subscription.update"
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )

    mock_api_usage.return_value = 12_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()

    # Then
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages_with_bad_plan(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=10_000,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=30),
        current_billing_term_ends_at=now + timedelta(hours=6),
    )
    organisation.subscription.subscription_id = "fancy_sub_id23"
    organisation.subscription.plan = "some-bad-plan-someone-randomly-made"
    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    mocker.patch("organisations.chargebee.chargebee.chargebee.Subscription.retrieve")
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee.Subscription.update"
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )

    mock_api_usage.return_value = 12_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()

    # Then
    # Since the plan is not known ahead of time, it isn't charged.
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_restrict_use_due_to_api_limit_grace_period_over(
    mocker: MockerFixture,
    organisation: Organisation,
    freezer: FrozenDateTimeFactory,
    mailoutbox: list[EmailMultiAlternatives],
    admin_user: FFAdminUser,
    staff_user: FFAdminUser,
) -> None:
    # Given
    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    now = timezone.now()
    organisation2 = Organisation.objects.create(name="Org #2")
    organisation3 = Organisation.objects.create(name="Org #3")
    organisation4 = Organisation.objects.create(name="Org #4")
    organisation5 = Organisation.objects.create(name="Org #5")

    for org in [
        organisation,
        organisation2,
        organisation3,
        organisation4,
        organisation5,
    ]:
        OrganisationSubscriptionInformationCache.objects.create(
            organisation=org,
            allowed_seats=10,
            allowed_projects=3,
            allowed_30d_api_calls=10_000,
            chargebee_email="test@example.com",
        )
        org.subscription.subscription_id = "fancy_sub_id23"
        org.subscription.plan = FREE_PLAN_ID
        org.subscription.save()

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 12_005

    # Add users to test email delivery
    for org in [organisation2, organisation3, organisation4, organisation5]:
        admin_user.add_organisation(org, role=OrganisationRole.ADMIN)
        staff_user.add_organisation(org, role=OrganisationRole.USER)

    organisation5.subscription.plan = "scale-up-v2"
    organisation5.subscription.payment_method = CHARGEBEE
    organisation5.subscription.subscription_id = "subscription-id"
    organisation5.subscription.save()

    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation,
        percent_usage=100,
    )
    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation,
        percent_usage=120,
    )
    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation2,
        percent_usage=100,
    )

    # Should be ignored, since percent usage is less than 100.
    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation3,
        percent_usage=90,
    )

    # Should be ignored, since not on a free plan.
    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation5,
        percent_usage=120,
    )

    now = now + timedelta(days=API_USAGE_GRACE_PERIOD + 1)
    freezer.move_to(now)

    # Should be ignored, since the notify period is too recent.
    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation3,
        percent_usage=120,
    )

    # When
    restrict_use_due_to_api_limit_grace_period_over()

    # Then
    organisation.refresh_from_db()
    organisation2.refresh_from_db()
    organisation3.refresh_from_db()
    organisation4.refresh_from_db()
    organisation5.refresh_from_db()

    # Organisation without breaching 100 percent usage is ok.
    assert organisation3.stop_serving_flags is False
    assert organisation3.block_access_to_admin is False
    assert getattr(organisation3, "api_limit_access_block", None) is None

    # Organisation which is still in the grace period is ok.
    assert organisation4.stop_serving_flags is False
    assert organisation4.block_access_to_admin is False
    assert getattr(organisation4, "api_limit_access_block", None) is None

    # Organisation which is not on the free plan is ok.
    assert organisation5.stop_serving_flags is False
    assert organisation5.block_access_to_admin is False
    assert getattr(organisation5, "api_limit_access_block", None) is None

    # Organisations that breached 100 are blocked.
    assert organisation.stop_serving_flags is True
    assert organisation.block_access_to_admin is True
    assert organisation.api_limit_access_block
    assert organisation2.stop_serving_flags is True
    assert organisation2.block_access_to_admin is True
    assert organisation2.api_limit_access_block

    client_mock.get_identity_flags.call_args_list == [
        call(
            f"org.{organisation.id}",
            traits={
                "organisation_id": organisation.id,
                "subscription.plan": organisation.subscription.plan,
            },
        ),
        call(
            f"org.{organisation2.id}",
            traits={
                "organisation_id": organisation2.id,
                "subscription.plan": organisation2.subscription.plan,
            },
        ),
    ]

    assert len(mailoutbox) == 2
    email1 = mailoutbox[0]
    assert email1.subject == "Flagsmith API use has been blocked due to overuse"
    assert email1.body == render_to_string(
        "organisations/api_flags_blocked_notification.txt",
        context={"organisation": organisation},
    )
    email2 = mailoutbox[1]
    assert email2.subject == "Flagsmith API use has been blocked due to overuse"
    assert email2.body == render_to_string(
        "organisations/api_flags_blocked_notification.txt",
        context={"organisation": organisation2},
    )

    assert len(email2.alternatives) == 1
    assert len(email2.alternatives[0]) == 2
    assert email2.alternatives[0][1] == "text/html"

    assert email2.alternatives[0][0] == render_to_string(
        "organisations/api_flags_blocked_notification.html",
        context={"organisation": organisation2},
    )
    assert email2.from_email == "noreply@flagsmith.com"
    assert email2.to == ["admin@example.com", "staff@example.com"]

    # Organisations that change their subscription are unblocked.
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()
    organisation.refresh_from_db()
    assert organisation.stop_serving_flags is False
    assert organisation.block_access_to_admin is False
    assert getattr(organisation, "api_limit_access_block", None) is None


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_restrict_use_due_to_api_limit_grace_period_over_missing_subscription_information_cache(
    mocker: MockerFixture,
    organisation: Organisation,
    freezer: FrozenDateTimeFactory,
    mailoutbox: list[EmailMultiAlternatives],
) -> None:
    # Given
    assert not organisation.has_subscription_information_cache()

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    now = timezone.now()
    organisation.subscription.subscription_id = "fancy_sub_id23"
    organisation.subscription.plan = FREE_PLAN_ID
    organisation.subscription.save()

    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation,
        percent_usage=120,
    )

    now = now + timedelta(days=API_USAGE_GRACE_PERIOD + 1)
    freezer.move_to(now)

    # When
    restrict_use_due_to_api_limit_grace_period_over()

    # Then
    organisation.refresh_from_db()

    # Organisations that missing the cache don't get blocked
    assert organisation.stop_serving_flags is False
    assert organisation.block_access_to_admin is False
    assert not hasattr(organisation, "api_limit_access_block")
    assert len(mailoutbox) == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_restrict_use_due_to_api_limit_grace_period_over_with_reduced_api_usage(
    mocker: MockerFixture,
    organisation: Organisation,
    freezer: FrozenDateTimeFactory,
    mailoutbox: list[EmailMultiAlternatives],
    inspecting_handler: logging.Handler,
) -> None:
    # Given
    assert not organisation.has_subscription_information_cache()

    from organisations.tasks import logger

    logger.addHandler(inspecting_handler)

    get_client_mock = mocker.patch("organisations.tasks.get_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_identity_flags.return_value.is_feature_enabled.return_value = True

    now = timezone.now()

    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=10_000,
        chargebee_email="test@example.com",
    )
    organisation.subscription.subscription_id = "fancy_sub_id23"
    organisation.subscription.plan = FREE_PLAN_ID
    organisation.subscription.save()

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 8000

    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation,
        percent_usage=120,
    )

    now = now + timedelta(days=API_USAGE_GRACE_PERIOD + 1)
    freezer.move_to(now)

    # When
    restrict_use_due_to_api_limit_grace_period_over()

    # Then
    organisation.refresh_from_db()

    # Organisations that missing the cache don't get blocked
    assert organisation.stop_serving_flags is False
    assert organisation.block_access_to_admin is False
    assert not hasattr(organisation, "api_limit_access_block")
    assert len(mailoutbox) == 0
    assert inspecting_handler.messages == [
        f"API use for organisation {organisation.id} has fallen to below limit, so not restricting use."
    ]


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_unrestrict_after_api_limit_grace_period_is_stale(
    organisation: Organisation,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Given
    now = timezone.now()
    organisation2 = Organisation.objects.create(name="Org #2")
    organisation3 = Organisation.objects.create(name="Org #3")
    organisation4 = Organisation.objects.create(name="Org #4")

    organisation.stop_serving_flags = True
    organisation.block_access_to_admin = True
    organisation.save()

    organisation2.stop_serving_flags = True
    organisation2.block_access_to_admin = True
    organisation2.save()

    organisation3.stop_serving_flags = True
    organisation3.block_access_to_admin = True
    organisation3.save()

    organisation4.stop_serving_flags = True
    organisation4.block_access_to_admin = True
    organisation4.save()

    # Create access blocks for the first three, excluding the 4th.
    APILimitAccessBlock.objects.create(organisation=organisation)
    APILimitAccessBlock.objects.create(organisation=organisation2)
    APILimitAccessBlock.objects.create(organisation=organisation3)

    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation,
        percent_usage=100,
    )
    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation,
        percent_usage=120,
    )
    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation2,
        percent_usage=100,
    )

    now = now + timedelta(days=32)
    freezer.move_to(now)

    # Exclude the organisation since there's a recent notification.
    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation3,
        percent_usage=120,
    )

    # When
    unrestrict_after_api_limit_grace_period_is_stale()

    # Then
    organisation.refresh_from_db()
    organisation2.refresh_from_db()
    organisation3.refresh_from_db()
    organisation4.refresh_from_db()

    # Organisations with stale notifications revert to access.
    assert organisation.stop_serving_flags is False
    assert organisation.block_access_to_admin is False
    assert organisation2.stop_serving_flags is False
    assert organisation2.block_access_to_admin is False
    assert getattr(organisation, "api_limit_access_block", None) is None
    assert getattr(organisation2, "api_limit_access_block", None) is None

    # Organisations with recent API usage notifications are blocked.
    assert organisation3.stop_serving_flags is True
    assert organisation3.block_access_to_admin is True
    assert organisation3.api_limit_access_block

    # Organisations without api limit access blocks stay blocked.
    assert organisation4.stop_serving_flags is True
    assert organisation4.block_access_to_admin is True
    assert getattr(organisation4, "api_limit_access_block", None) is None


def test_register_recurring_tasks(
    mocker: MockerFixture, settings: SettingsWrapper
) -> None:
    # Given
    settings.ENABLE_API_USAGE_ALERTING = True
    register_task_mock = mocker.patch("organisations.tasks.register_recurring_task")

    # When
    register_recurring_tasks()

    # Then
    # Check when the tasks have been registered
    register_task_mock.call_args_list == [
        call(run_every=timedelta(seconds=43200)),
        call(run_every=timedelta(seconds=1800)),
        call(run_every=timedelta(seconds=43200)),
        call(run_every=timedelta(seconds=43200)),
    ]

    # And check which tasks were passed in
    register_task_mock.return_value.call_args_list == [
        call(handle_api_usage_notifications),
        call(charge_for_api_call_count_overages),
        call(restrict_use_due_to_api_limit_grace_period_over),
        call(unrestrict_after_api_limit_grace_period_is_stale),
    ]

import uuid
from datetime import timedelta
from unittest.mock import MagicMock, call

import pytest
from dateutil.relativedelta import relativedelta
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from freezegun.api import FrozenDateTimeFactory
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from core.helpers import get_current_site_url
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
    OrganisationBreachedGracePeriod,
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
    SubscriptionCacheEntity,
)
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata
from organisations.task_helpers import (
    handle_api_usage_notification_for_organisation,
)
from organisations.tasks import (  # type: ignore[attr-defined]
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
    update_organisation_subscription_information_api_usage_cache,
    update_organisation_subscription_information_cache,
    update_organisation_subscription_information_cache_recurring,
)
from tests.types import EnableFeaturesFixture
from users.models import FFAdminUser


def test_send_org_over_limit_alert__free_subscription__sends_alert_with_free_plan_details(  # type: ignore[no-untyped-def]
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
def test_send_org_over_limit_alert__paid_subscription__sends_alert_with_subscription_details(  # type: ignore[no-untyped-def]
    organisation, subscription, mocker, SubscriptionMetadata
):
    # Given
    mocked_ffadmin_user = mocker.patch("organisations.tasks.FFAdminUser")
    max_seats = 10
    mocker.patch(
        "organisations.models.Subscription.get_subscription_metadata",
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


def test_finish_subscription_cancellation__cancelled_subscription__resets_to_free_plan(
    db: None,
) -> None:
    # Given
    organisation = Organisation.objects.create()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=5,
        allowed_30d_api_calls=1_000_000,
        allowed_projects=None,
        api_calls_24h=30_000,
        api_calls_7d=210_000,
        api_calls_30d=900_000,
        chargebee_email="foo@example.com",
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
    organisation.subscription_information_cache.refresh_from_db()

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

    # The CB / limit data on the subscription information cache object is reset
    assert organisation.subscription_information_cache.chargebee_email is None
    assert (
        organisation.subscription_information_cache.allowed_30d_api_calls
        == MAX_API_CALLS_IN_FREE_PLAN
    )
    assert organisation.subscription_information_cache.allowed_projects == 1
    assert (
        organisation.subscription_information_cache.allowed_seats
        == MAX_SEATS_IN_FREE_PLAN
    )

    # But the usage data isn't
    assert organisation.subscription_information_cache.api_calls_24h == 30_000
    assert organisation.subscription_information_cache.api_calls_7d == 210_000
    assert organisation.subscription_information_cache.api_calls_30d == 900_000


@pytest.mark.freeze_time("2023-01-19T09:12:34+00:00")
def test_finish_subscription_cancellation__multiple_organisations__removes_excess_users_for_cancelled_only(
    db: None, mocker: MockerFixture
) -> None:
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


def test_send_org_subscription_cancelled_alert__valid_organisation__sends_cancellation_email(
    mocker: MockerFixture, settings: SettingsWrapper
) -> None:
    # Given
    send_mail_mock = mocker.patch("organisations.tasks.send_mail")

    recipient = "foo@bar.com"
    settings.ORG_SUBSCRIPTION_CANCELLED_ALERT_RECIPIENT_LIST = [recipient]

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
        recipient_list=[recipient],
        fail_silently=True,
    )


def test_handle_api_usage_notification_for_organisation__billing_starts_at_is_none__logs_warning(
    organisation: Organisation,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given
    api_usage_mock = mocker.patch("organisations.task_helpers.get_current_api_usage")
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.subscription_id = "fancy_id"
    organisation.subscription.save()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=None,
        current_billing_term_ends_at=None,
    )

    # When
    handle_api_usage_notification_for_organisation(organisation)

    # Then
    api_usage_mock.assert_not_called()
    assert log.events == [
        {
            "level": "error",
            "event": "notification.missing_billing_starts_at",
            "organisation__id": organisation.id,
        }
    ]


def test_handle_api_usage_notification_for_organisation__cancellation_date_is_set__skips_notification(
    organisation: Organisation,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given
    usage = 25
    allowance = 1_000_000

    organisation.subscription.plan = SCALE_UP
    organisation.subscription.subscription_id = "fancy_id"
    organisation.subscription.cancellation_date = timezone.now()
    organisation.subscription.save()
    mock_api_usage = mocker.patch("organisations.task_helpers.get_current_api_usage")
    mock_api_usage.return_value = usage

    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_30d_api_calls=allowance,
        api_calls_30d=usage,
    )

    # When
    handle_api_usage_notification_for_organisation(organisation)

    # Then
    assert OrganisationAPIUsageNotification.objects.count() == 0

    assert not any(e["level"] == "error" for e in log.events)


def test_handle_api_usage_notification_for_organisation__billing_starts_at_over_12_months_ago__uses_12_month_offset(
    organisation: Organisation,
    mocker: MockerFixture,
) -> None:
    # Given
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.subscription_id = "fancy_id"
    organisation.subscription.save()

    billing_term_starts_at = timezone.now() - relativedelta(days=367)
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_30d_api_calls=1_000_000,
        current_billing_term_starts_at=billing_term_starts_at,
        api_calls_30d=1_900_000,
    )

    mock_api_usage = mocker.patch("organisations.task_helpers.get_current_api_usage")
    mock_api_usage.return_value = 2_000_000

    organisation.refresh_from_db()

    # When
    handle_api_usage_notification_for_organisation(organisation)

    # Then
    mock_api_usage.assert_called_once_with(
        organisation.id, billing_term_starts_at + relativedelta(months=12)
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications__feature_flag_is_off__skips_processing(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
) -> None:
    # Given
    now = timezone.now()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_30d_api_calls=100,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=45),
        current_billing_term_ends_at=now + timedelta(days=320),
        api_calls_30d=110,
    )
    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_not_called()

    assert len(mailoutbox) == 0
    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 0
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications__usage_below_100_percent__sends_90_percent_notification(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    now = timezone.now()
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.subscription_id = "fancy_id"
    organisation.subscription.save()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_30d_api_calls=100,
        current_billing_term_starts_at=now - timedelta(days=45),
        current_billing_term_ends_at=now + timedelta(days=320),
        api_calls_30d=90,
    )
    mock_api_usage = mocker.patch(
        "organisations.task_helpers.get_current_api_usage",
    )
    mock_api_usage.return_value = 91
    enable_features("api_usage_alerting")

    assert not OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # Create an OrganisationApiUsageNotification object for another organisation
    # to verify that only the correct organisation's notifications are taken into
    # account.
    another_organisation = Organisation.objects.create(name="Another Organisation")
    OrganisationAPIUsageNotification.objects.create(
        organisation=another_organisation,
        percent_usage=100,
        notified_at=now - timedelta(days=1),
    )

    # When
    handle_api_usage_notifications()

    # Then
    assert len(mock_api_usage.call_args_list) == 1

    # We only care about the call for the main organisation,
    # not the call for 'another_organisation'
    assert mock_api_usage.call_args_list[0].args == (
        organisation.id,
        now - timedelta(days=14),
    )

    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == "Flagsmith API use has reached 90%"
    assert email.body == render_to_string(
        "organisations/api_usage_notification.txt",
        context={
            "organisation": organisation,
            "matched_threshold": 90,
            "usage_url": f"{get_current_site_url()}/organisation/{organisation.id}/usage",
        },
    )

    assert len(email.alternatives) == 1
    assert len(email.alternatives[0]) == 2
    assert email.alternatives[0][1] == "text/html"

    assert email.alternatives[0][0] == render_to_string(
        "organisations/api_usage_notification.html",
        context={
            "organisation": organisation,
            "matched_threshold": 90,
            "usage_url": f"{get_current_site_url()}/organisation/{organisation.id}/usage",
        },
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

    assert api_usage_notification.percent_usage == 90  # type: ignore[union-attr]

    # Now re-run the usage to make sure the notification isn't resent.
    handle_api_usage_notifications()

    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )
    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation
        ).first()
        == api_usage_notification
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications__usage_below_alert_thresholds__sends_no_email(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
    enable_features: EnableFeaturesFixture,
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
        api_calls_30d=70,
    )
    mock_api_usage = mocker.patch(
        "organisations.task_helpers.get_current_api_usage",
    )
    usage = 21
    assert usage < min(API_USAGE_ALERT_THRESHOLDS)
    mock_api_usage.return_value = usage
    enable_features("api_usage_alerting")

    assert not OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # When
    handle_api_usage_notifications()

    # Then
    assert len(mailoutbox) == 0

    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 0
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications__usage_above_100_percent__sends_limit_notification(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    usage = 105
    allowance = 100

    now = timezone.now()
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.subscription_id = "fancy_id"
    organisation.subscription.save()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_30d_api_calls=allowance,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=45),
        current_billing_term_ends_at=now + timedelta(days=320),
        api_calls_30d=usage,
    )
    mock_api_usage = mocker.patch(
        "organisations.task_helpers.get_current_api_usage",
    )
    mock_api_usage.return_value = usage
    enable_features("api_usage_alerting")

    assert not OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_called_once_with(organisation.id, now - timedelta(days=14))

    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == "Flagsmith API use has reached 100%"
    assert email.body == render_to_string(
        "organisations/api_usage_notification_limit.txt",
        context={
            "organisation": organisation,
            "matched_threshold": 100,
            "usage_url": f"{get_current_site_url()}/organisation/{organisation.id}/usage",
        },
    )

    assert len(email.alternatives) == 1
    assert len(email.alternatives[0]) == 2
    assert email.alternatives[0][1] == "text/html"
    assert email.alternatives[0][0] == render_to_string(
        "organisations/api_usage_notification_limit.html",
        context={
            "organisation": organisation,
            "matched_threshold": 100,
            "usage_url": f"{get_current_site_url()}/organisation/{organisation.id}/usage",
        },
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

    assert api_usage_notification.percent_usage == 100  # type: ignore[union-attr]

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
def test_handle_api_usage_notifications__processing_error__logs_error_message(
    mocker: MockerFixture,
    organisation: Organisation,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given
    now = timezone.now()
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.subscription_id = "fancy_id"
    organisation.subscription.save()
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_30d_api_calls=100,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=45),
        current_billing_term_ends_at=now + timedelta(days=320),
        api_calls_30d=100,
    )

    get_client_mock = mocker.patch("organisations.tasks.get_openfeature_client")
    client_mock = MagicMock()
    get_client_mock.return_value = client_mock
    client_mock.get_boolean_value.return_value = True

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
    assert len(caplog.messages) == 1
    error_message = caplog.messages[0].split("\n")[0]

    assert (
        error_message
        == f"Error processing api usage for organisation {organisation.id}"
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_handle_api_usage_notifications__free_account_over_limit__sends_limit_notification_with_grace_period(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    allowance = MAX_SEATS_IN_FREE_PLAN
    usage = MAX_API_CALLS_IN_FREE_PLAN + 5_000

    now = timezone.now()
    assert organisation.is_paid is False
    assert organisation.subscription.is_free_plan is True
    assert organisation.subscription.max_api_calls == MAX_API_CALLS_IN_FREE_PLAN

    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_30d_api_calls=allowance,
        api_calls_30d=usage,
    )

    mock_api_usage = mocker.patch(
        "organisations.task_helpers.get_current_api_usage",
    )
    mock_api_usage.return_value = usage
    enable_features("api_usage_alerting")

    assert not OrganisationAPIUsageNotification.objects.filter(
        organisation=organisation,
    ).exists()

    # When
    handle_api_usage_notifications()

    # Then
    mock_api_usage.assert_called_once_with(organisation.id, now - timedelta(days=30))

    assert len(mailoutbox) == 1
    email = mailoutbox[0]
    assert email.subject == "Flagsmith API use has reached 100%"
    assert email.body == render_to_string(
        "organisations/api_usage_notification_limit.txt",
        context={
            "organisation": organisation,
            "matched_threshold": 100,
            "grace_period": True,
            "url": get_current_site_url(),
            "usage_url": f"{get_current_site_url()}/organisation/{organisation.id}/usage",
        },
    )

    assert len(email.alternatives) == 1
    assert len(email.alternatives[0]) == 2
    assert email.alternatives[0][1] == "text/html"

    assert email.alternatives[0][0] == render_to_string(
        "organisations/api_usage_notification_limit.html",
        context={
            "organisation": organisation,
            "matched_threshold": 100,
            "grace_period": True,
            "url": get_current_site_url(),
            "usage_url": f"{get_current_site_url()}/organisation/{organisation.id}/usage",
        },
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

    assert api_usage_notification.percent_usage == 100  # type: ignore[union-attr]

    # Now re-run the usage to make sure the notification isn't resent.
    handle_api_usage_notifications()

    assert (
        OrganisationAPIUsageNotification.objects.filter(
            organisation=organisation,
        ).count()
        == 1
    )

    assert OrganisationAPIUsageNotification.objects.first() == api_usage_notification


def test_handle_api_usage_notifications__missing_info_cache__skips_processing(
    mocker: MockerFixture,
    organisation: Organisation,
    mailoutbox: list[EmailMultiAlternatives],
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    organisation.subscription.plan = SCALE_UP
    organisation.subscription.save()

    assert organisation.has_subscription_information_cache() is False

    mock_api_usage = mocker.patch(
        "organisations.task_helpers.get_current_api_usage",
    )
    enable_features("api_usage_alerting")

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


@pytest.mark.parametrize("plan", ("scale-up", "scale-up-v2", "scale-up-v3"))
@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__scale_up_plan__charges_correct_addon_quantity(
    organisation: Organisation,
    mocker: MockerFixture,
    plan: str,
    enable_features: EnableFeaturesFixture,
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
    organisation.subscription.plan = plan
    organisation.subscription.save()

    # In order to cover an edge case found in production use, we make the
    # notification date just outside the previous 30 days, because we want
    # to make sure that we cover the case where someone with very high usage
    # is notified in the first day of their subscription period (in a 31-day
    # month).
    notification_date = now - (timedelta(days=30) + timedelta(minutes=30))
    assert notification_date > now - relativedelta(months=1)

    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=notification_date,
    )

    mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.retrieve",
        autospec=True,
    )
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )
    enable_features("api_usage_overage_charges")

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 212_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

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
    assert api_billing.organisation == organisation  # type: ignore[union-attr]
    assert api_billing.api_overage == 200_000  # type: ignore[union-attr]
    assert api_billing.immediate_invoice is False  # type: ignore[union-attr]
    assert api_billing.billed_at == now  # type: ignore[union-attr]


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__cancellation_date_set__skips_charging(
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
    organisation.subscription.cancellation_date = timezone.now()
    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

    # Then
    assert OrganisationAPIBilling.objects.count() == 0
    mock_api_usage.assert_not_called()


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__flagsmith_feature_disabled__skips_charging(
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

    mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.retrieve",
        autospec=True,
    )
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 212_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

    # Then
    # No charges are applied to the account.
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__within_grace_period__creates_breached_record_without_charging(
    organisation: Organisation,
    mocker: MockerFixture,
    enable_features: EnableFeaturesFixture,
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

    enable_features("api_usage_overage_charges")

    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )
    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    # Set the return value to something less than 200% of base rate
    mock_api_usage.return_value = 115_000
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

    # Then
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0
    assert organisation.breached_grace_period


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__grace_period_previously_breached__charges_overage(
    organisation: Organisation,
    mocker: MockerFixture,
    enable_features: EnableFeaturesFixture,
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

    OrganisationBreachedGracePeriod.objects.create(organisation=organisation)
    enable_features("api_usage_overage_charges")

    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )
    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    # Set the return value to something less than 200% of base rate
    mock_api_usage.return_value = 115_000
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

    # Then
    # Since the OrganisationBreachedGracePeriod was created already
    # the charges go through.
    mock_chargebee_update.assert_called_once_with(
        "fancy_sub_id23",
        {
            "addons": [{"id": "additional-api-scale-up-monthly", "quantity": 1}],
            "prorate": False,
            "invoice_immediately": False,
        },
    )
    assert OrganisationAPIBilling.objects.count() == 1


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__uncovered_plan__does_not_charge(
    organisation: Organisation,
    mocker: MockerFixture,
    enable_features: EnableFeaturesFixture,
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

    enable_features("api_usage_overage_charges")

    mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.retrieve",
        autospec=True,
    )
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 12_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

    # Then
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__usage_under_api_limit__does_not_charge(
    organisation: Organisation,
    mocker: MockerFixture,
    enable_features: EnableFeaturesFixture,
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

    enable_features("api_usage_overage_charges")

    mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.retrieve",
        autospec=True,
    )
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 2_000
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

    # Then
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__startup_plan__charges_correct_addon_quantity(
    organisation: Organisation,
    mocker: MockerFixture,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    now = timezone.now()
    current_billing_term_starts_at = now - timedelta(days=30)
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100_000,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=current_billing_term_starts_at,
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

    enable_features("api_usage_overage_charges")
    mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.retrieve",
        autospec=True,
    )
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 202_005
    assert OrganisationAPIBilling.objects.count() == 0

    # address a bug where we didn't filter for the current organisation
    # when selecting related billing records
    unrelated_organisation = Organisation.objects.create(name="Unrelated Organisation")
    OrganisationAPIBilling.objects.create(
        organisation=unrelated_organisation,
        api_overage=123_000_000,
        billed_at=current_billing_term_starts_at + timedelta(minutes=60),
    )

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

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

    assert OrganisationAPIBilling.objects.count() == 2
    api_billing = OrganisationAPIBilling.objects.filter(
        organisation=organisation
    ).first()
    assert api_billing
    assert api_billing.organisation == organisation
    assert api_billing.api_overage == 200_000
    assert api_billing.immediate_invoice is False
    assert api_billing.billed_at == now

    # Now attempt to rebill the account should fail
    calls_mock = mocker.patch(
        "organisations.tasks.add_100k_api_calls_start_up",
    )
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]
    assert OrganisationAPIBilling.objects.filter(organisation=organisation).count() == 1
    calls_mock.assert_not_called()


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__non_standard_plan__logs_unknown_plan_warning(
    organisation: Organisation,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    enable_features: EnableFeaturesFixture,
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
    organisation.subscription.plan = "nonstandard-v2"
    organisation.subscription.save()
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=100,
        notified_at=now,
    )

    enable_features("api_usage_overage_charges")
    mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.retrieve",
        autospec=True,
    )
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 202_005

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

    # Then
    mock_chargebee_update.assert_not_called()
    assert caplog.messages == [
        "Unknown subscription plan when trying to bill for overages "
        f"organisation.id={organisation.id} "
        "organisation.subscription.plan='nonstandard-v2'"
    ]

    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__billing_exception__logs_error_and_does_not_charge(
    organisation: Organisation,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    enable_features: EnableFeaturesFixture,
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

    enable_features("api_usage_overage_charges")
    mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.retrieve",
        autospec=True,
    )
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 202_005
    mocker.patch(
        "organisations.tasks.add_100k_api_calls_start_up",
        side_effect=ValueError("An error occurred"),
    )

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

    # Then
    assert caplog.messages[0].startswith(
        f"Unable to charge organisation {organisation.id} due to billing error"
    )
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__startup_plan_with_existing_billing__charges_remaining_overage(
    organisation: Organisation,
    mocker: MockerFixture,
    enable_features: EnableFeaturesFixture,
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

    enable_features("api_usage_overage_charges")
    mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.retrieve",
        autospec=True,
    )
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )
    mock_api_usage.return_value = 202_005
    assert OrganisationAPIBilling.objects.count() == 1

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

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
def test_charge_for_api_call_count_overages__yearly_account__does_not_charge(
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

    mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.retrieve",
        autospec=True,
    )
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )

    mock_api_usage.return_value = 12_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

    # Then
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_charge_for_api_call_count_overages__bad_plan_name__does_not_charge(
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

    mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.retrieve",
        autospec=True,
    )
    mock_chargebee_update = mocker.patch(
        "organisations.chargebee.chargebee.chargebee_client.Subscription.update",
        autospec=True,
    )

    mock_api_usage = mocker.patch(
        "organisations.tasks.get_current_api_usage",
    )

    mock_api_usage.return_value = 12_005
    assert OrganisationAPIBilling.objects.count() == 0

    # When
    charge_for_api_call_count_overages()  # type: ignore[no-untyped-call]

    # Then
    # Since the plan is not known ahead of time, it isn't charged.
    mock_chargebee_update.assert_not_called()
    assert OrganisationAPIBilling.objects.count() == 0


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_restrict_use_due_to_api_limit_grace_period_over__multiple_organisations__blocks_only_eligible(
    mocker: MockerFixture,
    organisation: Organisation,
    freezer: FrozenDateTimeFactory,
    mailoutbox: list[EmailMultiAlternatives],
    admin_user: FFAdminUser,
    staff_user: FFAdminUser,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(
        "api_limiting_stop_serving_flags",
        "api_limiting_block_access_to_admin",
    )

    now = timezone.now()
    organisation2 = Organisation.objects.create(name="Org #2")
    organisation3 = Organisation.objects.create(name="Org #3")
    organisation4 = Organisation.objects.create(name="Org #4")
    organisation5 = Organisation.objects.create(name="Org #5")
    organisation6 = Organisation.objects.create(name="Org #6")

    for org in [
        organisation,
        organisation2,
        organisation3,
        organisation4,
        organisation5,
        organisation6,
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
    for org in [
        organisation2,
        organisation3,
        organisation4,
        organisation5,
        organisation6,
    ]:
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

    # Should be immediately blocked because they've previously breached the grace
    # period
    OrganisationAPIUsageNotification.objects.create(
        notified_at=now,
        organisation=organisation6,
        percent_usage=120,
    )
    OrganisationBreachedGracePeriod.objects.create(organisation=organisation6)

    # When
    restrict_use_due_to_api_limit_grace_period_over()

    # Then
    organisation.refresh_from_db()
    organisation2.refresh_from_db()
    organisation3.refresh_from_db()
    organisation4.refresh_from_db()
    organisation5.refresh_from_db()
    organisation6.refresh_from_db()

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
    assert organisation6.stop_serving_flags is True
    assert organisation6.block_access_to_admin is True
    assert organisation6.api_limit_access_block

    assert len(mailoutbox) == 3
    email1 = mailoutbox[0]
    assert email1.subject == "Flagsmith API use has been blocked due to overuse"
    assert email1.body == render_to_string(
        "organisations/api_flags_blocked_notification.txt",
        context={
            "organisation": organisation,
            "url": get_current_site_url(),
            "usage_url": f"{get_current_site_url()}/organisation/{organisation.id}/usage",
        },
    )
    email2 = mailoutbox[1]
    assert email2.subject == "Flagsmith API use has been blocked due to overuse"
    assert email2.body == render_to_string(
        "organisations/api_flags_blocked_notification.txt",
        context={
            "organisation": organisation2,
            "url": get_current_site_url(),
            "usage_url": f"{get_current_site_url()}/organisation/{organisation2.id}/usage",
        },
    )

    assert len(email2.alternatives) == 1
    assert len(email2.alternatives[0]) == 2
    assert email2.alternatives[0][1] == "text/html"

    assert email2.alternatives[0][0] == render_to_string(
        "organisations/api_flags_blocked_notification.html",
        context={
            "organisation": organisation2,
            "grace_period": False,
            "url": get_current_site_url(),
            "usage_url": f"{get_current_site_url()}/organisation/{organisation2.id}/usage",
        },
    )
    assert email2.from_email == "noreply@flagsmith.com"
    assert email2.to == ["admin@example.com", "staff@example.com"]

    email3 = mailoutbox[2]
    assert email3.subject == "Flagsmith API use has been blocked due to overuse"
    assert len(email3.alternatives) == 1
    assert len(email3.alternatives[0]) == 2
    assert email3.alternatives[0][1] == "text/html"

    assert email3.alternatives[0][0] == render_to_string(
        "organisations/api_flags_blocked_notification.html",
        context={
            "organisation": organisation6,
            "grace_period": False,
            "usage_url": f"{get_current_site_url()}/organisation/{organisation6.id}/usage",
            "url": get_current_site_url(),
        },
    )
    assert email3.from_email == "noreply@flagsmith.com"
    assert email3.to == ["admin@example.com", "staff@example.com"]

    # Organisations that change their subscription are unblocked.
    organisation.subscription.plan = "scale-up-v2"
    organisation.subscription.save()
    organisation.refresh_from_db()
    assert organisation.stop_serving_flags is False
    assert organisation.block_access_to_admin is False
    assert getattr(organisation, "api_limit_access_block", None) is None


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_restrict_use_due_to_api_limit_grace_period_over__previously_breached__blocks_immediately(
    mocker: MockerFixture,
    organisation: Organisation,
    freezer: FrozenDateTimeFactory,
    mailoutbox: list[EmailMultiAlternatives],
    admin_user: FFAdminUser,
    staff_user: FFAdminUser,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features(
        "api_limiting_stop_serving_flags",
        "api_limiting_block_access_to_admin",
    )

    now = timezone.now()

    OrganisationBreachedGracePeriod.objects.create(organisation=organisation)
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
    mock_api_usage.return_value = 12_005

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
    now = now + timedelta(days=API_USAGE_GRACE_PERIOD - 1)
    freezer.move_to(now)

    # When
    restrict_use_due_to_api_limit_grace_period_over()

    # Then
    organisation.refresh_from_db()

    assert organisation.stop_serving_flags is True
    assert organisation.block_access_to_admin is True
    assert organisation.api_limit_access_block


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_restrict_use_due_to_api_limit_grace_period_over__missing_subscription_cache__does_not_block(
    organisation: Organisation,
    freezer: FrozenDateTimeFactory,
    mailoutbox: list[EmailMultiAlternatives],
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    assert not organisation.has_subscription_information_cache()
    enable_features(
        "api_limiting_stop_serving_flags",
        "api_limiting_block_access_to_admin",
    )

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
def test_restrict_use_due_to_api_limit_grace_period_over__reduced_api_usage__does_not_block(
    mocker: MockerFixture,
    organisation: Organisation,
    freezer: FrozenDateTimeFactory,
    mailoutbox: list[EmailMultiAlternatives],
    caplog: pytest.LogCaptureFixture,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    assert not organisation.has_subscription_information_cache()

    enable_features(
        "api_limiting_stop_serving_flags",
        "api_limiting_block_access_to_admin",
    )

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
    assert caplog.messages == [
        f"API use for organisation {organisation.id} has fallen to below limit, so not restricting use."
    ]


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_unrestrict_after_api_limit_grace_period_is_stale__stale_notifications__unblocks_organisations(
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


def test_register_recurring_tasks__alerting_enabled__registers_all_tasks(
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


def test_update_organisation_subscription_information_cache_recurring__called__delegates_to_cache_task(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_update = mocker.patch(
        "organisations.tasks.update_organisation_subscription_information_cache"
    )

    # When
    update_organisation_subscription_information_cache_recurring()

    # Then
    assert mock_update.call_args_list == [mocker.call()]


def test_update_organisation_subscription_information_api_usage_cache__called__calls_update_caches_with_api_usage(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_update_caches = mocker.patch(
        "organisations.tasks.subscription_info_cache.update_caches"
    )

    # When
    update_organisation_subscription_information_api_usage_cache()

    # Then
    assert mock_update_caches.call_args_list == [
        mocker.call(SubscriptionCacheEntity.API_USAGE)
    ]


def test_update_organisation_subscription_information_cache__called__calls_update_caches_with_chargebee_and_api_usage(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_update_caches = mocker.patch(
        "organisations.tasks.subscription_info_cache.update_caches"
    )

    # When
    update_organisation_subscription_information_cache()

    # Then
    assert mock_update_caches.call_args_list == [
        mocker.call(
            SubscriptionCacheEntity.CHARGEBEE, SubscriptionCacheEntity.API_USAGE
        )
    ]

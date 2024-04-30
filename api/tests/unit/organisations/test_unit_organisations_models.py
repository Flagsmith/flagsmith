from datetime import datetime, timedelta
from unittest import mock

import pytest
from django.conf import settings
from django.utils import timezone
from pytest_mock import MockerFixture
from rest_framework.test import override_settings

from environments.models import Environment
from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.models import (
    OranisationAPIUsageNotification,
    Organisation,
    OrganisationSubscriptionInformationCache,
    Subscription,
)
from organisations.subscriptions.constants import (
    CHARGEBEE,
    FREE_PLAN_ID,
    FREE_PLAN_SUBSCRIPTION_METADATA,
    MAX_API_CALLS_IN_FREE_PLAN,
    MAX_SEATS_IN_FREE_PLAN,
    TRIAL_SUBSCRIPTION_ID,
    XERO,
)
from organisations.subscriptions.exceptions import (
    SubscriptionDoesNotSupportSeatUpgrade,
)
from organisations.subscriptions.metadata import BaseSubscriptionMetadata
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata


def test_organisation_has_paid_subscription_true(db: None) -> None:
    # Given
    organisation = Organisation.objects.create(name="Test org")
    Subscription.objects.filter(organisation=organisation).update(
        subscription_id="subscription_id"
    )

    # refresh organisation to load subscription
    organisation.refresh_from_db()

    # Then
    assert organisation.has_paid_subscription()


def test_organisation_has_paid_subscription_missing_subscription_id(db: None) -> None:
    # Given
    organisation = Organisation.objects.create(name="Test org")
    assert (
        Subscription.objects.filter(organisation=organisation).first().subscription_id
        is None
    )

    # Then
    assert not organisation.has_paid_subscription()


@mock.patch("organisations.models.cancel_chargebee_subscription")
def test_organisation_cancel_subscription_cancels_chargebee_subscription(
    mocked_cancel_chargebee_subscription,
    organisation: Organisation,
):
    # Given
    Subscription.objects.filter(organisation=organisation).update(
        subscription_id="subscription_id", payment_method=CHARGEBEE
    )
    subscription = Subscription.objects.get(organisation=organisation)

    # refresh organisation to load subscription
    organisation.refresh_from_db()

    # When
    organisation.cancel_subscription()

    # Then
    mocked_cancel_chargebee_subscription.assert_called_once_with(
        subscription.subscription_id
    )
    # refresh subscription object
    subscription.refresh_from_db()
    # Subscription has been immediately transformed to free.
    assert subscription.cancellation_date is None
    assert subscription.subscription_id is None
    assert subscription.billing_status is None
    assert subscription.payment_method is None
    assert subscription.plan == FREE_PLAN_ID


def test_organisation_rebuild_environment_document_on_stop_serving_flags_changed(
    environment: Environment, organisation: Organisation, mocker: MockerFixture
):
    # Given
    mocked_rebuild_environment_document = mocker.patch(
        "environments.tasks.rebuild_environment_document"
    )
    assert organisation.stop_serving_flags is False

    # When
    organisation.stop_serving_flags = True
    organisation.save()

    # Then
    mocked_rebuild_environment_document.delay.assert_called_once_with(
        args=(environment.id,)
    )


def test_organisation_rebuild_environment_document_on_stop_serving_flags_unchanged(
    environment: Environment, organisation: Organisation, mocker: MockerFixture
):
    # Given
    mocked_rebuild_environment_document = mocker.patch(
        "environments.tasks.rebuild_environment_document"
    )

    # When saving something irrelevant
    organisation.alerted_over_plan_limit = True
    organisation.save()

    # Then the task should not be called
    mocked_rebuild_environment_document.delay.assert_not_called()


def test_organisation_over_plan_seats_limit_returns_false_if_not_over_plan_seats_limit(
    organisation, chargebee_subscription, mocker
):
    # Given
    seats = 200
    mocked_get_subscription_metadata = mocker.patch(
        "organisations.models.Subscription.get_subscription_metadata",
        autospec=True,
        return_value=BaseSubscriptionMetadata(seats=seats),
    )
    # Then
    assert organisation.over_plan_seats_limit() is False
    mocked_get_subscription_metadata.assert_called_once_with(chargebee_subscription)


def test_organisation_over_plan_seats_limit_returns_true_if_over_plan_seats_limit(
    organisation, chargebee_subscription, mocker, admin_user
):
    # Given
    seats = 0
    mocked_get_subscription_metadata = mocker.patch(
        "organisations.models.Subscription.get_subscription_metadata",
        autospec=True,
        return_value=BaseSubscriptionMetadata(seats=seats),
    )
    # Then
    assert organisation.over_plan_seats_limit() is True
    mocked_get_subscription_metadata.assert_called_once_with(chargebee_subscription)


def test_organisation_over_plan_seats_no_subscription(organisation, mocker, admin_user):
    # Given
    organisation.subscription.max_seats = 0
    organisation.subscription.save()

    mocked_get_subscription_metadata = mocker.patch(
        "organisations.models.Subscription.get_subscription_metadata",
        autospec=True,
    )
    # Then
    assert organisation.over_plan_seats_limit() is True
    mocked_get_subscription_metadata.assert_not_called()


def test_organisation_is_auto_seat_upgrade_available(organisation, settings):
    # Given
    plan = "Scale-Up"
    subscription_id = "subscription-id"
    settings.AUTO_SEAT_UPGRADE_PLANS = [plan]

    Subscription.objects.filter(organisation=organisation).update(
        subscription_id=subscription_id, plan=plan
    )

    # refresh organisation to load subscription
    organisation.refresh_from_db()

    # Then
    assert organisation.is_auto_seat_upgrade_available() is True


def test_organisation_default_subscription_have_one_max_seat(
    organisation: Organisation,
) -> None:
    # Given
    subscription = Subscription.objects.get(organisation=organisation)

    # Then
    assert subscription.max_seats == 1


@override_settings(MAILERLITE_API_KEY="some-test-key")
def test_updating_subscription_id_calls_mailer_lite_update_organisation_users(
    mocker, db, organisation, subscription
):
    # Given
    mocked_mailer_lite = mocker.MagicMock()
    mocker.patch("organisations.models.MailerLite", return_value=mocked_mailer_lite)

    # When
    subscription.subscription_id = "some-id"
    subscription.save()

    # Then
    mocked_mailer_lite.update_organisation_users.assert_called_with(organisation.id)


@override_settings(MAILERLITE_API_KEY="some-test-key")
def test_updating_a_cancelled_subscription_calls_mailer_lite_update_organisation_users(
    mocker, db, organisation, subscription
):
    # Given
    mocked_mailer_lite = mocker.MagicMock()
    mocker.patch("organisations.models.MailerLite", return_value=mocked_mailer_lite)

    subscription.cancellation_date = datetime.now()
    subscription.save()

    # reset the mock to remove the call by saving the subscription above
    mocked_mailer_lite.reset_mock()

    # When
    subscription.cancellation_date = None
    subscription.save()

    # Then
    mocked_mailer_lite.update_organisation_users.assert_called_with(organisation.id)


@override_settings(MAILERLITE_API_KEY="some-test-key")
def test_cancelling_a_subscription_calls_mailer_lite_update_organisation_users(
    mocker, db, organisation, subscription
):
    # Given

    mocked_mailer_lite = mocker.MagicMock()
    mocker.patch("organisations.models.MailerLite", return_value=mocked_mailer_lite)

    # When
    subscription.cancellation_date = datetime.now()
    subscription.save()

    # Then
    mocked_mailer_lite.update_organisation_users.assert_called_once_with(
        organisation.id
    )


def test_organisation_is_paid_returns_false_if_subscription_does_not_exists(db):
    # Given
    organisation = Organisation.objects.create(name="Test org")
    # Then
    assert organisation.is_paid is False


def test_organisation_is_paid_returns_true_if_active_subscription_exists(
    organisation, chargebee_subscription
):
    # When/Then
    assert organisation.is_paid is True


def test_organisation_is_paid_returns_false_if_cancelled_subscription_exists(
    organisation, chargebee_subscription
):
    # Given
    organisation = Organisation.objects.create(name="Test org")
    chargebee_subscription.cancellation_date = datetime.now()
    chargebee_subscription.save()

    # Then
    assert organisation.is_paid is False


def test_organisation_subscription_get_subscription_metadata_returns_cb_metadata_for_cb_subscription(
    organisation: Organisation,
    mocker: MockerFixture,
):
    # Given
    seats = 10
    api_calls = 50000000
    projects = 10
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=seats,
        allowed_30d_api_calls=api_calls,
        allowed_projects=projects,
    )
    expected_metadata = ChargebeeObjMetadata(
        seats=seats, api_calls=api_calls, projects=projects
    )
    mocker.patch("organisations.models.is_saas", return_value=True)
    Subscription.objects.filter(organisation=organisation).update(
        plan="scale-up-v2",
        subscription_id="subscription-id",
        payment_method=CHARGEBEE,
    )
    organisation.subscription.refresh_from_db()

    # When
    subscription_metadata = organisation.subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == expected_metadata


def test_organisation_subscription_get_subscription_metadata_returns_xero_metadata_for_xero_sub(
    mocker: MockerFixture,
):
    # Given
    subscription = Subscription(
        payment_method=XERO, subscription_id="xero-subscription", plan="enterprise"
    )
    expected_metadata = XeroSubscriptionMetadata(
        seats=subscription.max_seats, api_calls=subscription.max_api_calls
    )
    mocker.patch("organisations.models.is_saas", return_value=True)

    # When
    subscription_metadata = subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == expected_metadata


def test_organisation_subscription_get_subscription_metadata_returns_free_plan_metadata_for_no_plan():
    # Given
    subscription = Subscription()

    # When
    subscription_metadata = subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == FREE_PLAN_SUBSCRIPTION_METADATA


@pytest.mark.parametrize(
    "subscription_id, plan, max_seats, expected_seats, expected_projects",
    (
        (
            None,
            "free",
            10,
            MAX_SEATS_IN_FREE_PLAN,
            settings.MAX_PROJECTS_IN_FREE_PLAN,
        ),
        ("anything", "enterprise", 20, 20, None),
        (TRIAL_SUBSCRIPTION_ID, "enterprise", 20, 20, None),
    ),
)
def test_organisation_get_subscription_metadata_for_enterprise_self_hosted_licenses(
    organisation: Organisation,
    subscription_id: str | None,
    plan: str,
    max_seats: int,
    expected_seats: int,
    expected_projects: int | None,
    mocker: MockerFixture,
) -> None:
    """
    Specific test to make sure that we can manually add subscriptions to
    enterprise self-hosted deployments and the values stored in the django
    database will be correctly used.
    """
    # Given
    Subscription.objects.filter(organisation=organisation).update(
        subscription_id=subscription_id, plan=plan, max_seats=max_seats
    )
    organisation.subscription.refresh_from_db()
    mocker.patch("organisations.models.is_saas", return_value=False)
    mocker.patch("organisations.models.is_enterprise", return_value=True)

    # When
    subscription_metadata = organisation.subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata.projects == expected_projects
    assert subscription_metadata.seats == expected_seats


@pytest.mark.parametrize(
    "subscription_id, plan, max_seats, max_api_calls, expected_seats, "
    "expected_api_calls, expected_projects",
    (
        (
            None,
            "free",
            10,
            5000000,
            MAX_SEATS_IN_FREE_PLAN,
            MAX_API_CALLS_IN_FREE_PLAN,
            settings.MAX_PROJECTS_IN_FREE_PLAN,
        ),
        ("anything", "enterprise", 20, 5000000, 20, 5000000, None),
        (TRIAL_SUBSCRIPTION_ID, "enterprise", 20, 5000000, 20, 5000000, None),
    ),
)
def test_organisation_get_subscription_metadata_for_manually_added_enterprise_saas_licenses(
    organisation: Organisation,
    subscription_id: str | None,
    plan: str,
    max_seats: int,
    max_api_calls: int,
    expected_seats: int,
    expected_api_calls: int,
    expected_projects: int | None,
    mocker: MockerFixture,
) -> None:
    """
    Specific test to make sure that we can manually add subscriptions to
    the SaaS platform and the values stored in the Django database will
    be correctly used.
    """
    # Given
    Subscription.objects.filter(organisation=organisation).update(
        subscription_id=subscription_id,
        plan=plan,
        max_seats=max_seats,
        max_api_calls=max_api_calls,
    )
    organisation.subscription.refresh_from_db()
    mocker.patch("organisations.models.is_saas", return_value=True)

    # When
    subscription_metadata = organisation.subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata.projects == expected_projects
    assert subscription_metadata.seats == expected_seats
    assert subscription_metadata.api_calls == expected_api_calls


def test_organisation_get_subscription_metadata_for_self_hosted_open_source(
    organisation: Organisation, mocker: MockerFixture
) -> None:
    """
    Open source should ignore the details provided in the
    subscription and always return the free plan metadata.
    """
    # Given
    Subscription.objects.filter(organisation=organisation).update(
        max_seats=100,
        max_api_calls=10000000000,
        plan="enterprise",
        subscription_id="subscription-id",
    )
    organisation.subscription.refresh_from_db()
    mocker.patch("organisations.models.is_enterprise", return_value=False)
    mocker.patch("organisations.models.is_saas", return_value=False)

    # When
    subscription_metadata = organisation.subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == FREE_PLAN_SUBSCRIPTION_METADATA


def test_organisation_subscription_add_single_seat_calls_correct_chargebee_method_for_upgradable_plan(
    mocker, settings
):
    # Given
    settings.AUTO_SEAT_UPGRADE_PLANS = ["scale-up"]

    subscription_id = "subscription-id"
    subscription = Subscription(subscription_id=subscription_id, plan="scale-up")

    mocked_add_single_seat = mocker.patch(
        "organisations.models.add_single_seat", autospec=True
    )
    # When
    subscription.add_single_seat()

    # Then
    mocked_add_single_seat.assert_called_once_with(subscription_id)


def test_organisation_subscription_add_single_seat_raises_error_for_non_upgradable_plan(
    mocker, settings
):
    # Given
    settings.AUTO_SEAT_UPGRADE_PLANS = ["scale-up"]

    subscription_id = "subscription-id"
    subscription = Subscription(
        subscription_id=subscription_id, plan="not-a-scale-up-plan"
    )

    mocked_add_single_seat = mocker.patch(
        "organisations.models.add_single_seat", autospec=True
    )

    # When
    with pytest.raises(SubscriptionDoesNotSupportSeatUpgrade):
        subscription.add_single_seat()

    # and add_single_seat was not called
    mocked_add_single_seat.assert_not_called()


def test_organisation_update_clears_environment_caches(
    mocker, organisation, environment
):
    # Given
    mock_environment_cache = mocker.patch("organisations.models.environment_cache")

    # When
    organisation.name += "update"
    organisation.save()

    # Then
    mock_environment_cache.delete_many.assert_called_once_with([environment.api_key])


def test_reset_of_api_notifications(organisation: Organisation) -> None:
    # Given
    now = timezone.now()
    osic = OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=45),
        current_billing_term_ends_at=now + timedelta(days=320),
    )

    # Create a notification which should be deleted shortly.
    OranisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=90,
        notified_at=now,
    )

    # Keep a notification which should not be deleted.
    organisation2 = Organisation.objects.create(name="Test org2")
    oapiun = OranisationAPIUsageNotification.objects.create(
        organisation=organisation2,
        percent_usage=90,
        notified_at=now,
    )

    # When
    osic.allowed_30d_api_calls *= 2
    osic.save()

    # Then
    assert OranisationAPIUsageNotification.objects.count() == 1
    assert OranisationAPIUsageNotification.objects.first() == oapiun

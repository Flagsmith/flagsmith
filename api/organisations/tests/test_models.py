from datetime import datetime
from unittest import mock

import pytest
from django.test import TestCase
from rest_framework.test import override_settings

from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.models import (
    TRIAL_SUBSCRIPTION_ID,
    Organisation,
    OrganisationSubscriptionInformationCache,
    Subscription,
)
from organisations.subscriptions.constants import (
    CHARGEBEE,
    FREE_PLAN_SUBSCRIPTION_METADATA,
    XERO,
)
from organisations.subscriptions.exceptions import (
    SubscriptionDoesNotSupportSeatUpgrade,
)
from organisations.subscriptions.metadata import BaseSubscriptionMetadata
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata


@pytest.mark.django_db
class OrganisationTestCase(TestCase):
    def test_can_create_organisation_with_and_without_webhook_notification_email(self):
        organisation_1 = Organisation.objects.create(name="Test org")
        organisation_2 = Organisation.objects.create(
            name="Test org with webhook email",
            webhook_notification_email="test@org.com",
        )

        self.assertTrue(organisation_1.name)
        self.assertTrue(organisation_2.name)

    def test_has_subscription_true(self):
        # Given
        organisation = Organisation.objects.create(name="Test org")
        Subscription.objects.filter(organisation=organisation).update(
            subscription_id="subscription_id"
        )

        # refresh organisation to load subscription
        organisation.refresh_from_db()

        # Then
        assert organisation.has_subscription()

    def test_has_subscription_missing_subscription_id(self):
        # Given
        organisation = Organisation.objects.create(name="Test org")

        # Then
        assert not organisation.has_subscription()

    @mock.patch("organisations.models.cancel_chargebee_subscription")
    def test_cancel_subscription_cancels_chargebee_subscription(
        self, mocked_cancel_chargebee_subscription
    ):
        # Given
        organisation = Organisation.objects.create(name="Test org")

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
        assert subscription.cancellation_date


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


class SubscriptionTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test org")

    def tearDown(self) -> None:
        Subscription.objects.all().delete()

    def test_max_seats_set_as_one_if_subscription_has_no_subscription_id(self):
        # Given
        subscription = Subscription.objects.get(organisation=self.organisation)

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


def test_subscription_get_subscription_metadata_returns_cb_metadata_for_cb_subscription(
    mocker,
):
    # Given
    subscription = Subscription(
        payment_method=CHARGEBEE, subscription_id="cb-subscription"
    )

    expected_metadata = ChargebeeObjMetadata(seats=10, api_calls=50000000, projects=10)
    mock_cb_get_subscription_metadata = mocker.patch(
        "organisations.models.get_subscription_metadata"
    )
    mock_cb_get_subscription_metadata.return_value = expected_metadata

    # When
    subscription_metadata = subscription.get_subscription_metadata()

    # Then
    mock_cb_get_subscription_metadata.assert_called_once_with(
        subscription.subscription_id
    )
    assert subscription_metadata == expected_metadata


def test_subscription_get_subscription_metadata_returns_xero_metadata_for_xero_sub():
    # Given
    subscription = Subscription(
        payment_method=XERO, subscription_id="xero-subscription"
    )

    expected_metadata = XeroSubscriptionMetadata(
        seats=subscription.max_seats, api_calls=subscription.max_api_calls
    )

    # When
    subscription_metadata = subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == expected_metadata


def test_subscription_get_subscription_metadata_returns_free_plan_metadata_for_no_plan():
    # Given
    subscription = Subscription()

    # When
    subscription_metadata = subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == FREE_PLAN_SUBSCRIPTION_METADATA


def test_subscription_get_subscription_metadata_for_trial():
    # Given
    max_seats = 10
    max_api_calls = 1000000
    subscription = Subscription(
        subscription_id=TRIAL_SUBSCRIPTION_ID,
        max_seats=max_seats,
        max_api_calls=max_api_calls,
        payment_method=None,
    )

    # When
    subscription_metadata = subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata.seats == max_seats
    assert subscription_metadata.api_calls == max_api_calls
    assert subscription_metadata.projects is None


def test_subscription_add_single_seat_calls_correct_chargebee_method_for_upgradable_plan(
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


def test_subscription_add_single_seat_raises_error_for_non_upgradable_plan(
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


@pytest.mark.parametrize(
    "allowed_calls_30d, actual_calls_30d, expected_overage",
    ((1000000, 500000, 0), (1000000, 1100000, 100000), (0, 100000, 100000)),
)
def test_subscription_get_api_call_overage(
    organisation, subscription, allowed_calls_30d, actual_calls_30d, expected_overage
):
    # Given
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_30d_api_calls=allowed_calls_30d,
        api_calls_30d=actual_calls_30d,
    )

    # When
    overage = subscription.get_api_call_overage()

    # Then
    assert overage == expected_overage

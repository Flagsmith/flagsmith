from datetime import datetime

import pytest
from django.test import TestCase
from rest_framework.test import override_settings

from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.models import Organisation, Subscription
from organisations.subscriptions.constants import (
    CHARGEBEE,
    FREE_PLAN_SUBSCRIPTION_METADATA,
    XERO,
)
from organisations.subscriptions.dataclasses import BaseSubscriptionMetadata


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
        Subscription.objects.create(
            organisation=organisation, subscription_id="subscription_id"
        )

        # Then
        assert organisation.has_subscription()

    def test_has_subscription_missing_subscription(self):
        # Given
        organisation = Organisation.objects.create(name="Test org")

        # Then
        assert not organisation.has_subscription()

    def test_has_subscription_missing_subscription_id(self):
        # Given
        organisation = Organisation.objects.create(name="Test org")
        Subscription.objects.create(organisation=organisation)

        # Then
        assert not organisation.has_subscription()


class SubscriptionTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test org")

    def tearDown(self) -> None:
        Subscription.objects.all().delete()

    def test_max_seats_set_as_one_if_subscription_has_no_subscription_id(self):
        # Given
        subscription = Subscription(organisation=self.organisation)

        # When
        subscription.save()

        # Then
        assert subscription.max_seats == 1


@override_settings(MAILERLITE_API_KEY="some-test-key")
def test_creating_a_subscription_calls_mailer_lite_update_organisation_users(
    mocker, db
):
    # Given
    organisation = Organisation.objects.create(name="Test org")
    mocked_mailer_lite = mocker.MagicMock()
    mocker.patch("organisations.models.MailerLite", return_value=mocked_mailer_lite)

    # When
    Subscription.objects.create(organisation=organisation)

    # Then
    mocked_mailer_lite.update_organisation_users.assert_called_with(organisation.id)


@override_settings(MAILERLITE_API_KEY="some-test-key")
def test_updating_a_cancelled_subscription_calls_mailer_lite_update_organisation_users(
    mocker, db
):
    # Given
    organisation = Organisation.objects.create(name="Test org")
    mocked_mailer_lite = mocker.MagicMock()
    mocker.patch("organisations.models.MailerLite", return_value=mocked_mailer_lite)

    subscription = Subscription.objects.create(
        organisation=organisation, cancellation_date=datetime.now()
    )

    # reset the mock as it will have been called on subscription create above
    mocked_mailer_lite.reset_mock()

    # When
    subscription.cancellation_date = None
    subscription.save()

    # Then
    mocked_mailer_lite.update_organisation_users.assert_called_with(organisation.id)


@override_settings(MAILERLITE_API_KEY="some-test-key")
def test_cancelling_a_subscription_calls_mailer_lite_update_organisation_users(
    mocker, db
):
    # Given

    mocked_mailer_lite = mocker.MagicMock()
    mocker.patch("organisations.models.MailerLite", return_value=mocked_mailer_lite)
    organisation = Organisation.objects.create(name="Test org")
    subscription = Subscription.objects.create(organisation=organisation)

    # When
    subscription.cancellation_date = datetime.now()
    subscription.save()

    # Then
    mocked_mailer_lite.update_organisation_users.assert_called_with(organisation.id)
    # once for creating a subscription and second time for cancellation
    assert mocked_mailer_lite.update_organisation_users.call_count == 2


def test_organisation_is_paid_returns_false_if_subscription_does_not_exists(db):
    # Given
    organisation = Organisation.objects.create(name="Test org")
    # Then
    assert organisation.is_paid is False


def test_organisation_is_paid_returns_true_if_active_subscription_exists(db):
    # Given
    organisation = Organisation.objects.create(name="Test org")
    Subscription.objects.create(organisation=organisation, subscription_id="random_id")
    # Then
    assert organisation.is_paid is True


def test_organisation_is_paid_returns_false_if_cancelled_subscription_exists(db):
    # Given
    organisation = Organisation.objects.create(name="Test org")
    Subscription.objects.create(
        organisation=organisation, cancellation_date=datetime.now()
    )
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

    expected_metadata = BaseSubscriptionMetadata(
        seats=subscription.max_seats,
        api_calls=subscription.max_api_calls,
        payment_source=XERO,
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

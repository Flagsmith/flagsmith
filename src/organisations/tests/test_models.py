from unittest import mock
from unittest.mock import call

import pytest
from django.test import TestCase

from organisations.models import Organisation, Subscription


@pytest.mark.django_db
class OrganisationTestCase(TestCase):
    def test_can_create_organisation_with_and_without_webhook_notification_email(self):
        organisation_1 = Organisation.objects.create(name="Test org")
        organisation_2 = Organisation.objects.create(name="Test org with webhook email",
                                                     webhook_notification_email="test@org.com")

        self.assertTrue(organisation_1.name)
        self.assertTrue(organisation_2.name)


class SubscriptionTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test org')

    def tearDown(self) -> None:
        Subscription.objects.all().delete()

    def test_max_seats_set_as_one_if_subscription_has_no_subscription_id(self):
        # Given
        subscription = Subscription(organisation=self.organisation)

        # When
        subscription.save()

        # Then
        assert subscription.max_seats == 1

    @mock.patch('organisations.signals.get_plan_id_from_subscription')
    @mock.patch('organisations.signals.get_max_seats_for_plan')
    def test_plan_and_max_seats_set_on_save(self, mock_max_seats, mock_get_plan):
        # Given
        subscription_id = 'test-subscription-id'
        subscription = Subscription(organisation=self.organisation, subscription_id=subscription_id)

        plan_id = 'test-plan'
        mock_get_plan.return_value = plan_id

        max_seats = 3
        mock_max_seats.return_value = max_seats

        # When
        subscription.save()

        # Then
        mock_get_plan.assert_called_with(subscription_id)
        assert subscription.plan == plan_id

        # and
        mock_max_seats.assert_called_with(plan_id)
        assert subscription.max_seats == max_seats

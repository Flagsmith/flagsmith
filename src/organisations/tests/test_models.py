from unittest import mock

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

    @mock.patch('organisations.models.get_max_seats_for_plan')
    def test_max_seats_set_for_subscription_on_save_if_not_already_set(self, mock_max_seats):
        # Given
        plan_id = 'test-plan'
        max_seats = 3
        organisation = Organisation.objects.create(name='Test org')
        subscription = Subscription(organisation=organisation, plan=plan_id)
        mock_max_seats.return_value = max_seats

        # When
        subscription.save()

        # Then
        mock_max_seats.assert_called_with(plan_id)

        # and
        assert subscription.max_seats == max_seats

    @mock.patch('organisations.models.get_max_seats_for_plan')
    def test_max_seats_not_set_for_subscription_on_save_if_already_set(self, mock_max_seats):
        # Given
        plan_id = 'test-plan'
        max_seats = 3
        organisation = Organisation.objects.create(name='Test org')
        subscription = Subscription(organisation=organisation, plan=plan_id, max_seats=max_seats)

        # When
        subscription.save()

        # Then
        mock_max_seats.assert_not_called()

        # and
        assert subscription.max_seats == max_seats


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

    @mock.patch('organisations.signals.get_max_seats_for_plan')
    def test_max_seats_set_for_subscription_on_create(self, mock_max_seats):
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

    @mock.patch('organisations.signals.get_max_seats_for_plan')
    def test_max_seats_not_set_for_subscription_on_update_if_same_plan(self, mock_max_seats):
        # Given
        plan_id = 'test-plan'
        max_seats = 3
        mock_max_seats.return_value = max_seats

        organisation = Organisation.objects.create(name='Test org')
        subscription = Subscription.objects.create(organisation=organisation, plan=plan_id)

        # When
        subscription.save()

        # Then
        mock_max_seats.assert_called_once()

        # and
        assert subscription.max_seats == max_seats

    @mock.patch('organisations.signals.get_max_seats_for_plan')
    def test_max_seats_set_for_subscription_on_save_if_plan_changed(self, mock_max_seats):
        # Given
        old_plan_id = 'test-plan'
        new_plan_id = 'new-test-plan'
        old_max_seats = 3
        mock_max_seats.return_value = old_max_seats

        new_max_seats = 5
        mock_max_seats.return_value = new_max_seats

        organisation = Organisation.objects.create(name='Test org')
        subscription = Subscription.objects.create(organisation=organisation, plan=old_plan_id)

        # When
        subscription.plan = new_plan_id
        subscription.save()

        # Then
        calls = [call(old_plan_id), call(new_plan_id)]
        mock_max_seats.assert_has_calls(calls)

        # and
        assert subscription.max_seats == new_max_seats


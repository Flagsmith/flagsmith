import json
from datetime import datetime
from unittest import TestCase, mock

import pytest
from django.urls import reverse
from pytz import UTC
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation, OrganisationRole
from users.models import Invite, FFAdminUser
from util.tests import Helper


@pytest.mark.django_db
class OrganisationTestCase(TestCase):
    post_template = '{ "name" : "%s", "webhook_notification_email": "%s" }'
    put_template = '{ "name" : "%s"}'

    def setUp(self):
        self.client = APIClient()
        self.user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=self.user)

    def tearDown(self) -> None:
        Helper.clean_up()

    def test_should_return_organisation_list_when_requested(self):
        # Given
        organisation = Organisation.objects.create(name='Test org')
        self.user.add_organisation(organisation)

        # When
        response = self.client.get('/api/v1/organisations/')

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data and response.data['count'] == 1

    def test_should_create_new_organisation(self):
        # Given
        org_name = 'Test create org'
        webhook_notification_email = 'test@email.com'
        url = reverse('api:v1:organisations:organisation-list')
        data = {
            'name': org_name,
            'webhook_notification_email': webhook_notification_email
        }

        # When
        response = self.client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert Organisation.objects.get(name=org_name).webhook_notification_email == webhook_notification_email

    def test_should_update_organisation_name(self):
        # Given
        original_organisation_name = "test org"
        new_organisation_name = "new test org"
        organisation = Organisation.objects.create(name=original_organisation_name)
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse('api:v1:organisations:organisation-detail', args=[organisation.pk])
        data = {
            'name': new_organisation_name
        }

        # When
        response = self.client.put(url, data=data)

        # Then
        organisation.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert organisation.name == new_organisation_name

    def test_should_invite_users(self):
        # Given
        org_name = "test_org"
        organisation = Organisation.objects.create(name=org_name)
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse('api:v1:organisations:organisation-invite', args=[organisation.pk])
        data = {
            'emails': ['test@example.com'],
            'frontend_base_url': 'https://example.com'
        }

        # When
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert Invite.objects.filter(email="test@example.com").exists()

    def test_should_fail_if_invite_exists_already(self):
        # Given
        organisation = Organisation.objects.create(name="test org")
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        email = "test_2@example.com"
        data = {
            'emails': [email],
            'frontend_base_url': 'https://example.com'
        }
        url = reverse('api:v1:organisations:organisation-invite', args=[organisation.pk])

        # When
        response_success = self.client.post(url, data=json.dumps(data), content_type='application/json')
        response_fail = self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert response_success.status_code == status.HTTP_201_CREATED
        assert response_fail.status_code == status.HTTP_400_BAD_REQUEST
        assert Invite.objects.filter(email=email, organisation=organisation).count() == 1

    def test_should_return_all_invites_and_can_resend(self):
        # Given
        organisation = Organisation.objects.create(name="Test org 2")
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)

        invite_1 = Invite.objects.create(email="test_1@example.com",
                                         frontend_base_url="https://www.example.com",
                                         organisation=organisation)
        invite_2 = Invite.objects.create(email="test_2@example.com",
                                         frontend_base_url="https://www.example.com",
                                         organisation=organisation)

        # When
        invite_list_response = self.client.get('/api/v1/organisations/%s/invites/' % organisation.id)
        invite_resend_response = self.client.post('/api/v1/organisations/%s/invites/%s/resend/' % (
            organisation.id, invite_1.id))

        # Then
        assert invite_list_response.status_code == status.HTTP_200_OK
        assert invite_resend_response.status_code == status.HTTP_200_OK

    def test_can_remove_a_user_from_an_organisation(self):
        # Given
        organisation = Organisation.objects.create(name='Test org')
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)

        user_2 = FFAdminUser.objects.create(email='test@example.com')
        user_2.add_organisation(organisation)

        url = reverse('api:v1:organisations:organisation-remove-users', args=[organisation.pk])

        data = [
            {'id': user_2.pk}
        ]

        # When
        res = self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert res.status_code == status.HTTP_200_OK
        assert organisation not in user_2.organisations.all()

    def test_can_invite_user_as_admin(self):
        # Given
        organisation = Organisation.objects.create(name='Test org')
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse('api:v1:organisations:organisation-invite', args=[organisation.pk])
        invited_email = 'test@example.com'

        data = {
            'invites': [{
                'email': invited_email,
                'role': OrganisationRole.ADMIN.name
            }],
            'frontend_base_url': 'http://blah.com'
        }

        # When
        self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert Invite.objects.filter(email=invited_email).exists()

        # and
        assert Invite.objects.get(email=invited_email).role == OrganisationRole.ADMIN.name

    def test_can_invite_user_as_user(self):
        # Given
        organisation = Organisation.objects.create(name='Test org')
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse('api:v1:organisations:organisation-invite', args=[organisation.pk])
        invited_email = 'test@example.com'

        data = {
            'invites': [{
                'email': invited_email,
                'role': OrganisationRole.USER.name
            }],
            'frontend_base_url': 'http://blah.com'
        }

        # When
        self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert Invite.objects.filter(email=invited_email).exists()

        # and
        assert Invite.objects.get(email=invited_email).role == OrganisationRole.USER.name

    @mock.patch('organisations.serializers.get_subscription_data_from_hosted_page')
    def test_update_subscription_gets_subscription_data_from_chargebee(self, mock_get_subscription_data):
        # Given
        organisation = Organisation.objects.create(name='Test org')
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse('api:v1:organisations:organisation-update-subscription', args=[organisation.pk])

        hosted_page_id = 'some-id'
        data = {
            'hosted_page_id': hosted_page_id
        }

        subscription_id = 'subscription-id'
        mock_get_subscription_data.return_value = {
            'subscription_id': subscription_id,
            'plan': 'plan-id',
            'max_seats': 3,
            'subscription_date': datetime.now(tz=UTC)
        }

        # When
        res = self.client.post(url, data=data)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        mock_get_subscription_data.assert_called_with(hosted_page_id=hosted_page_id)

        # and
        assert organisation.has_subscription() and organisation.subscription.subscription_id == subscription_id

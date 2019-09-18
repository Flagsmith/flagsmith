import json
from unittest import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation
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
        org_name = "Test create org"

        # When
        response = self.client.post('/api/v1/organisations/',
                                    data=self.post_template % (org_name, "test@email.com"),
                                    content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert Organisation.objects.get(name=org_name).webhook_notification_email

    def test_should_update_organisation_name(self):
        # Given
        original_organisation_name = "test org"
        new_organisation_name = "new test org"
        organisation = Organisation.objects.create(name=original_organisation_name)
        self.user.add_organisation(organisation)

        # When
        response = self.client.put('/api/v1/organisations/%s/' % organisation.id,
                                   data=self.put_template % new_organisation_name,
                                   content_type='application/json')

        # Then
        organisation.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert organisation.name == new_organisation_name

    def test_should_invite_users(self):
        # Given
        org_name = "test_org"
        organisation = Organisation.objects.create(name=org_name)
        self.user.add_organisation(organisation)

        # When
        response = self.client.post('/api/v1/organisations/%s/invite/' % organisation.id,
                                    data='{"emails":["test@example.com"], '
                                         '"frontend_base_url": "https://example.com"}',
                                    content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        invite = Invite.objects.get(email="test@example.com")
        # check hash was created
        assert invite.hash

    def test_should_fail_if_invite_exists_already(self):
        # Given
        organisation = Organisation.objects.create(name="test org")
        self.user.add_organisation(organisation)
        email = "test_2@example.com"
        data = '{"emails":["%s"], "frontend_base_url": "https://example.com"}' % email

        # When
        response_success = self.client.post('/api/v1/organisations/%s/invite/' % organisation.id,
                                            data=data,
                                            content_type='application/json')
        response_fail = self.client.post('/api/v1/organisations/%s/invite/' % organisation.id,
                                         data=data,
                                         content_type='application/json')

        # Then
        assert response_success.status_code == status.HTTP_201_CREATED
        assert response_fail.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in json.loads(response_fail.content)
        assert Invite.objects.filter(email=email, organisation=organisation).count() == 1

    def test_should_return_all_invites_and_can_resend(self):
        # Given
        organisation = Organisation.objects.create(name="Test org 2")
        self.user.add_organisation(organisation)

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
        self.user.add_organisation(organisation)

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

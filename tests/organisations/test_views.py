import json
from unittest import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation
from tests.utils import Helper
from users.models import Invite


class OrganisationTestCase(TestCase):
    post_template = '{ "name" : "%s", "webhook_notification_email": "%s" }'
    put_template = '{ "name" : "%s"}'

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)
        return client

    def test_should_return_organisation_list_when_requested(self):
        # Given
        client = self.set_up()

        # When
        response = client.get('/api/v1/organisations/')

        # Then
        self.assertEquals(response.status_code, 200)
        self.assertTrue('count' in response.data and response.data['count'] == 1)

    def test_should_create_new_organisation(self):
        # Given
        client = self.set_up()

        # When
        response = client.post('/api/v1/organisations/',
                               data=self.post_template % ("Test create org", "test@email.com"),
                               content_type='application/json')

        # Then
        self.assertEquals(response.status_code, 201)
        self.assertTrue(Organisation.objects.get(name="Test create org").webhook_notification_email)

    def test_should_update_organisation_name(self):
        client = self.set_up()

        # Given
        organisation = Organisation.objects.get(name="test org")
        # When
        ssg = 'ssg'
        response = client.put('/api/v1/organisations/%s/' % organisation.id,
                              data=self.put_template % ssg,
                              content_type='application/json')
        # Then
        organisation.refresh_from_db()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(organisation.name, ssg)

    def test_should_invite_users(self):
        # Given
        client = self.set_up()
        organisation = Organisation.objects.get(name="test org")

        # When
        response = client.post('/api/v1/organisations/%s/invite/' % organisation.id,
                               data='{"emails":["test@example.com"], '
                                    '"frontend_base_url": "https://example.com"}',
                               content_type='application/json')

        # Then
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        invite = Invite.objects.get(email="test@example.com")
        # check hash was created
        self.assertTrue(invite.hash)

    def test_should_fail_if_invite_exists_already(self):
        # Given
        client = self.set_up()
        organisation = Organisation.objects.get(name="test org")
        email = "test_2@example.com"
        data = '{"emails":["%s"], "frontend_base_url": "https://example.com"}' % email

        # When
        response_success = client.post('/api/v1/organisations/%s/invite/' % organisation.id,
                                       data=data,
                                       content_type='application/json')
        response_fail = client.post('/api/v1/organisations/%s/invite/' % organisation.id,
                                    data=data,
                                    content_type='application/json')

        # Then
        self.assertEquals(response_success.status_code, status.HTTP_201_CREATED)
        self.assertEquals(response_fail.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("error" in json.loads(response_fail.content))

        invites = Invite.objects.filter(email=email, organisation=organisation)
        self.assertEquals(len(invites), 1)

    def test_should_return_all_invites_and_can_resend(self):
        # Given
        client = self.set_up()
        organisation_2 = Organisation.objects.create(name="Test org 2")
        invite_1 = Invite.objects.create(email="test_1@example.com",
                                         frontend_base_url="https://www.example.com",
                                         organisation=organisation_2)
        invite_2 = Invite.objects.create(email="test_2@example.com",
                                         frontend_base_url="https://www.example.com",
                                         organisation=organisation_2)

        # When
        invite_list_response = client.get('/api/v1/organisations/%s/invites/' % organisation_2.id)
        invite_resend_response = client.post('/api/v1/organisations/%s/invites/%s/resend/' % (
            organisation_2.id, invite_1.id))

        # Then
        self.assertEquals(invite_list_response.status_code, status.HTTP_200_OK)
        self.assertEquals(invite_resend_response.status_code, status.HTTP_200_OK)
from unittest import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation, OrganisationRole
from users.models import FFAdminUser, Invite
from util.tests import Helper


@pytest.mark.django_db
class UserTestCase(TestCase):
    auth_base_url = '/api/v1/auth/'
    register_template = '{ ' \
                        '"email": "%s", ' \
                        '"first_name": "%s", ' \
                        '"last_name": "%s", ' \
                        '"password1": "%s", ' \
                        '"password2": "%s" ' \
                        '}'
    login_template = '{' \
                     '"email": "%s",' \
                     '"password": "%s"' \
                     '}'

    def setUp(self):
        self.client = APIClient()
        self.user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=self.user)

        self.organisation = Organisation.objects.create(name="test org")

    def tearDown(self) -> None:
        Helper.clean_up()

    def test_registration_and_login(self):
        Helper.generate_database_models()
        # When
        register_response = self.client.post(self.auth_base_url + "register/",
                                             data=self.register_template % ("johndoe@example.com",
                                                                            "john",
                                                                            "doe",
                                                                            "johndoe123",
                                                                            "johndoe123"),
                                             content_type='application/json')

        # Then
        self.assertEquals(register_response.status_code, status.HTTP_201_CREATED)
        self.assertIn("key", register_response.data)
        # Check user was created
        self.assertEquals(FFAdminUser.objects.filter(email="johndoe@example.com").count(), 1)
        user = FFAdminUser.objects.get(email="johndoe@example.com")
        organisation = Organisation(name="test org")
        organisation.save()
        user.organisation = organisation
        user.save()
        # Check user can login
        login_response = self.client.post(self.auth_base_url + "login/",
                                          data=self.login_template % (
                                              "johndoe@example.com", "johndoe123"),
                                          content_type='application/json')
        self.assertEquals(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("key", login_response.data)

        # verify key works on authenticated endpoint
        content = login_response.data
        organisations_response = self.client.get("/api/v1/organisations/",
                                                 HTTP_AUTHORIZATION="Token " + content['key'])
        self.assertEquals(organisations_response.status_code, status.HTTP_200_OK)

    def test_join_organisation(self):
        # Given
        invite = Invite.objects.create(email=self.user.email, organisation=self.organisation)
        url = reverse('api:v1:users:user-join-organisation', args=[invite.hash])

        # When
        response = self.client.post(url)
        self.user.refresh_from_db()

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert self.organisation in self.user.organisations.all()

    def test_cannot_join_organisation_with_different_email_address_than_invite(self):
        # Given
        invite = Invite.objects.create(email='some-other-email@test.com', organisation=self.organisation)
        url = reverse('api:v1:users:user-join-organisation', args=[invite.hash])

        # When
        res = self.client.post(url)

        # Then
        assert res.status_code == status.HTTP_400_BAD_REQUEST

        # and
        assert self.organisation not in self.user.organisations.all()

    def test_can_update_role_for_a_user_in_organisation(self):
        # Given
        organisation_user = FFAdminUser.objects.create(email='org_user@org.com')
        organisation_user.add_organisation(self.organisation)
        url = reverse('api:v1:organisations:organisation-users-update-role', args=[self.organisation.pk,
                                                                                   organisation_user.pk])
        data = {
            'role': OrganisationRole.ADMIN.name
        }

        # When
        res = self.client.post(url, data=data)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert organisation_user.get_organisation_role(self.organisation) == OrganisationRole.ADMIN.name

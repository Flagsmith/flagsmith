from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from organisations.models import Organisation
from tests.utils import Helper
from users.models import FFAdminUser, Invite


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

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)
        return client

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

        Helper.clean_up()

    def test_join_organisation(self):
        # Given
        client = self.set_up()
        organisation_2 = Organisation(name="test org 2")
        organisation_2.save()
        invite = Invite(email="test_user@test.com", organisation=organisation_2)
        invite.save()
        user = FFAdminUser.objects.get(email="test_user@test.com")
        token = Token(user=user)
        token.save()

        # When
        response = client.post("/api/v1/users/join/" + invite.hash + "/",
                               HTTP_AUTHORIZATION="Token " + token.key)
        user.refresh_from_db()

        # Then
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(user.organisations.all().count(), 2)
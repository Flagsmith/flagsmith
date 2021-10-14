import re
import time
from collections import ChainMap

import pyotp
from django.conf import settings
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, override_settings

from organisations.invites.models import Invite
from organisations.models import Organisation
from users.models import FFAdminUser


class AuthIntegrationTestCase(APITestCase):
    test_email = "test@example.com"
    password = FFAdminUser.objects.make_random_password()

    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test Organisation")

    def tearDown(self) -> None:
        FFAdminUser.objects.all().delete()

    def test_register_and_login_workflows(self):
        # try to register without first_name / last_name
        register_data = {
            "email": self.test_email,
            "password": self.password,
            "re_password": self.password,
        }
        register_url = reverse("api-v1:custom_auth:ffadminuser-list")
        register_response_fail = self.client.post(register_url, data=register_data)
        # should return 400
        assert register_response_fail.status_code == status.HTTP_400_BAD_REQUEST

        # now register with full data
        register_data["first_name"] = "test"
        register_data["last_name"] = "user"
        register_response_success = self.client.post(register_url, data=register_data)
        assert register_response_success.status_code == status.HTTP_201_CREATED
        assert register_response_success.json()["key"]

        # add delay to avoid HTTP_429 as we have throttle in place for login
        time.sleep(1)
        # now verify we can login with the same credentials
        new_login_data = {
            "email": self.test_email,
            "password": self.password,
        }
        login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")
        new_login_response = self.client.post(login_url, data=new_login_data)
        assert new_login_response.status_code == status.HTTP_200_OK
        assert new_login_response.json()["key"]

        # Oh no, we forgot our password
        reset_password_url = reverse("api-v1:custom_auth:ffadminuser-reset-password")
        reset_password_data = {"email": self.test_email}
        reset_password_response = self.client.post(
            reset_password_url, data=reset_password_data
        )
        # API docs are incorrect, 204 is the correct status code for this endpoint
        assert reset_password_response.status_code == status.HTTP_204_NO_CONTENT
        # verify that the user has been emailed with their reset code
        assert len(mail.outbox) == 1
        # get the url and grab the uid and token
        url = re.findall(r"http\:\/\/.*", mail.outbox[0].body)[0]
        split_url = url.split("/")
        uid = split_url[-2]
        token = split_url[-1]

        # confirm the reset and set the new password
        new_password = FFAdminUser.objects.make_random_password()
        reset_password_confirm_data = {
            "uid": uid,
            "token": token,
            "new_password": new_password,
            "re_new_password": new_password,
        }
        reset_password_confirm_url = reverse(
            "api-v1:custom_auth:ffadminuser-reset-password-confirm"
        )
        reset_password_confirm_response = self.client.post(
            reset_password_confirm_url, data=reset_password_confirm_data
        )
        assert reset_password_confirm_response.status_code == status.HTTP_204_NO_CONTENT

        # add delay to avoid HTTP_429 as we have throttle in place for login
        time.sleep(1)
        # now check we can login with the new details
        new_login_data = {
            "email": self.test_email,
            "password": new_password,
        }
        new_login_response = self.client.post(login_url, data=new_login_data)
        assert new_login_response.status_code == status.HTTP_200_OK
        assert new_login_response.json()["key"]

    @override_settings(ALLOW_REGISTRATION_WITHOUT_INVITE=False)
    def test_cannot_register_without_invite_if_disabled(self):
        # Given
        register_data = {
            "email": self.test_email,
            "password": self.password,
            "first_name": "test",
            "last_name": "register",
        }

        # When
        url = reverse("api-v1:custom_auth:ffadminuser-list")
        response = self.client.post(url, data=register_data)

        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @override_settings(ALLOW_REGISTRATION_WITHOUT_INVITE=False)
    def test_can_register_with_invite_if_registration_disabled_without_invite(self):
        # Given
        register_data = {
            "email": self.test_email,
            "password": self.password,
            "first_name": "test",
            "last_name": "register",
        }
        Invite.objects.create(email=self.test_email, organisation=self.organisation)

        # When
        url = reverse("api-v1:custom_auth:ffadminuser-list")
        response = self.client.post(url, data=register_data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED

    @override_settings(
        DJOSER=ChainMap(
            {"SEND_ACTIVATION_EMAIL": True, "SEND_CONFIRMATION_EMAIL": False},
            settings.DJOSER,
        )
    )
    def test_registration_and_login_with_user_activation_flow(self):
        """
        Test user registration and login flow via email activation.
        By default activation flow is disabled
        """

        # Given user registration data
        register_data = {
            "email": self.test_email,
            "password": self.password,
            "first_name": "test",
            "last_name": "register",
        }

        # When register
        register_url = reverse("api-v1:custom_auth:ffadminuser-list")
        result = self.client.post(
            register_url, data=register_data, status_code=status.HTTP_201_CREATED
        )

        # Then success and account inactive
        self.assertIn("key", result.data)
        self.assertIn("is_active", result.data)
        assert result.data["is_active"] == False

        new_user = FFAdminUser.objects.latest("id")
        self.assertEqual(new_user.email, register_data["email"])
        self.assertFalse(new_user.is_active)

        # And login should fail as we have not activated account yet
        # add delay to avoid HTTP_429 as we have throttle in place for login
        time.sleep(1)
        login_data = {
            "email": self.test_email,
            "password": self.password,
        }
        login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")
        failed_login_res = self.client.post(login_url, data=login_data)
        # should return 400
        assert failed_login_res.status_code == status.HTTP_400_BAD_REQUEST

        # verify that the user has been emailed activation email
        # and extract uid and token for account activation
        assert len(mail.outbox) == 1
        # get the url and grab the uid and token
        url = re.findall(r"http\:\/\/.*", mail.outbox[0].body)[0]
        split_url = url.split("/")
        uid = split_url[-2]
        token = split_url[-1]

        activate_data = {"uid": uid, "token": token}

        activate_url = reverse("api-v1:custom_auth:ffadminuser-activation")
        # And activate account
        self.client.post(
            activate_url, data=activate_data, status_code=status.HTTP_204_NO_CONTENT
        )

        time.sleep(1)
        # And login success
        login_result = self.client.post(login_url, data=login_data)
        assert login_result.status_code == status.HTTP_200_OK
        self.assertIn("key", login_result.data)

    def test_login_workflow_with_mfa_enabled(self):
        # register the user
        register_data = {
            "email": self.test_email,
            "password": self.password,
            "re_password": self.password,
            "first_name": "test",
            "last_name": "user",
        }
        register_url = reverse("api-v1:custom_auth:ffadminuser-list")
        register_response = self.client.post(register_url, data=register_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        key = register_response.json()["key"]

        # authenticate the test client
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        # create an MFA method
        create_mfa_method_url = reverse(
            "api-v1:custom_auth:mfa-activate", kwargs={"method": "app"}
        )
        create_mfa_response = self.client.post(create_mfa_method_url)
        assert create_mfa_response.status_code == status.HTTP_200_OK
        secret = create_mfa_response.json()["secret"]

        # confirm the MFA method
        totp = pyotp.TOTP(secret)
        confirm_mfa_data = {"code": totp.now()}
        confirm_mfa_method_url = reverse(
            "api-v1:custom_auth:mfa-activate-confirm", kwargs={"method": "app"}
        )
        confirm_mfa_method_response = self.client.post(
            confirm_mfa_method_url, data=confirm_mfa_data
        )
        assert confirm_mfa_method_response

        # now login should return an ephemeral token rather than a token
        login_data = {"email": self.test_email, "password": self.password}
        self.client.logout()
        login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")
        login_response = self.client.post(login_url, data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        ephemeral_token = login_response.json()["ephemeral_token"]

        # now we can confirm the login
        confirm_login_data = {"ephemeral_token": ephemeral_token, "code": totp.now()}
        login_confirm_url = reverse("api-v1:custom_auth:mfa-authtoken-login-code")
        login_confirm_response = self.client.post(
            login_confirm_url, data=confirm_login_data
        )
        assert login_confirm_response.status_code == status.HTTP_200_OK
        key = login_confirm_response.json()["key"]

        # and verify that we can use the token to access the API
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        current_user_url = reverse("api-v1:custom_auth:ffadminuser-me")
        current_user_response = self.client.get(current_user_url)
        assert current_user_response.status_code == status.HTTP_200_OK
        assert current_user_response.json()["email"] == self.test_email

    @override_settings()
    def test_throttle_login_workflows(self):
        # verify that a throttle rate exists already then set it
        # to something easier to reliably test
        assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login"]
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login"] = "1/sec"

        # register the user
        register_data = {
            "email": self.test_email,
            "password": self.password,
            "re_password": self.password,
            "first_name": "test",
            "last_name": "user",
        }
        register_url = reverse("api-v1:custom_auth:ffadminuser-list")
        register_response = self.client.post(register_url, data=register_data)
        assert register_response.status_code == status.HTTP_201_CREATED
        assert register_response.json()["key"]

        # since we're hitting login in other tests we need to ensure that the
        # first login request doesn't fail with HTTP_429
        time.sleep(1)
        # verify we can login with credentials
        login_data = {
            "email": self.test_email,
            "password": self.password,
        }
        login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")
        login_response = self.client.post(login_url, data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        assert login_response.json()["key"]

        # try login in again, should deny, current limit 1 per second
        login_response = self.client.post(login_url, data=login_data)
        assert login_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

import re

import time
import pyotp
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import FFAdminUser


class AuthIntegrationTestCase(APITestCase):
    login_url = "/api/v1/auth/login/"
    register_url = "/api/v1/auth/users/"
    reset_password_url = "/api/v1/auth/users/reset_password/"
    reset_password_confirm_url = "/api/v1/auth/users/reset_password_confirm/"
    current_user_url = f"{register_url}me/"
    test_email = "test@example.com"
    password = FFAdminUser.objects.make_random_password()

    def tearDown(self) -> None:
        FFAdminUser.objects.all().delete()

    def test_register_and_login_workflows(self):
        # try to register without first_name / last_name
        register_data = {
            "email": self.test_email,
            "password": self.password,
            "re_password": self.password,
        }
        register_response_fail = self.client.post(self.register_url, data=register_data)
        # should return 400
        assert register_response_fail.status_code == status.HTTP_400_BAD_REQUEST

        # now register with full data
        register_data["first_name"] = "test"
        register_data["last_name"] = "user"
        register_response_success = self.client.post(
            self.register_url, data=register_data
        )
        assert register_response_success.status_code == status.HTTP_201_CREATED
        assert register_response_success.json()["key"]

        # add delay to avoid HTTP_429 as we have throttle in place for login
        time.sleep(1)
        # now verify we can login with the same credentials
        new_login_data = {
            "email": self.test_email,
            "password": self.password,
        }
        new_login_response = self.client.post(self.login_url, data=new_login_data)
        assert new_login_response.status_code == status.HTTP_200_OK
        assert new_login_response.json()["key"]

        # Oh no, we forgot our password
        reset_password_data = {"email": self.test_email}
        reset_password_response = self.client.post(
            self.reset_password_url, data=reset_password_data
        )
        # API docs are incorrect, 204 is the correct status code for this endpoint
        assert reset_password_response.status_code == status.HTTP_204_NO_CONTENT
        # verify that the user has been emailed with their reset code
        assert len(mail.outbox) == 1
        # get the url and grab the uid and token
        url = re.findall("http\:\/\/.*", mail.outbox[0].body)[0]
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
        reset_password_confirm_response = self.client.post(
            self.reset_password_confirm_url, data=reset_password_confirm_data
        )
        assert reset_password_confirm_response.status_code == status.HTTP_204_NO_CONTENT

        # add delay to avoid HTTP_429 as we have throttle in place for login
        time.sleep(1)
        # now check we can login with the new details
        new_login_data = {
            "email": self.test_email,
            "password": new_password,
        }
        new_login_response = self.client.post(self.login_url, data=new_login_data)
        assert new_login_response.status_code == status.HTTP_200_OK
        assert new_login_response.json()["key"]

    def test_login_workflow_with_mfa_enabled(self):
        # register the user
        register_data = {
            "email": self.test_email,
            "password": self.password,
            "re_password": self.password,
            "first_name": "test",
            "last_name": "user",
        }
        register_response = self.client.post(
            self.register_url, data=register_data
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        key = register_response.json()["key"]

        # authenticate the test client
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

        # create an MFA method
        create_mfa_method_url = reverse("api-v1:custom_auth:mfa-activate", kwargs={"method": "app"})
        create_mfa_response = self.client.post(create_mfa_method_url)
        assert create_mfa_response.status_code == status.HTTP_200_OK
        secret = create_mfa_response.json()["secret"]

        # confirm the MFA method
        totp = pyotp.TOTP(secret)
        confirm_mfa_data = {
            "code": totp.now()
        }
        confirm_mfa_method_url = reverse("api-v1:custom_auth:mfa-activate-confirm", kwargs={"method": "app"})
        confirm_mfa_method_response = self.client.post(confirm_mfa_method_url, data=confirm_mfa_data)
        assert confirm_mfa_method_response

        # now login should return an ephemeral token rather than a token
        login_data = {
            "email": self.test_email,
            "password": self.password
        }
        self.client.logout()
        login_response = self.client.post(self.login_url, data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        ephemeral_token = login_response.json()["ephemeral_token"]

        # now we can confirm the login
        confirm_login_data = {
            "ephemeral_token": ephemeral_token,
            "code": totp.now()
        }
        login_confirm_url = reverse("api-v1:custom_auth:mfa-authtoken-login-code")
        login_confirm_response = self.client.post(login_confirm_url, data=confirm_login_data)
        assert login_confirm_response.status_code == status.HTTP_200_OK
        key = login_confirm_response.json()["key"]

        # and verify that we can use the token to access the API
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
        current_user_response = self.client.get(self.current_user_url)
        assert current_user_response.status_code == status.HTTP_200_OK
        assert current_user_response.json()["email"] == self.test_email

    def test_throttle_login_workflows(self):
        # register the user
        register_data = {
            "email": self.test_email,
            "password": self.password,
            "re_password": self.password,
            "first_name": "test",
            "last_name": "user",
        }
        register_response = self.client.post(
            self.register_url, data=register_data
        )
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
        login_response = self.client.post(self.login_url, data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        assert login_response.json()["key"]

        # try login in again, should deny, current limit 1 per second
        login_response = self.client.post(self.login_url, data=login_data)
        assert login_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

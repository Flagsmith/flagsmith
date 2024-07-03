import json
import re
from collections import ChainMap

import pyotp
from django.conf import settings
from django.core import mail
from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient, override_settings

from organisations.invites.models import Invite
from organisations.models import Organisation
from users.models import FFAdminUser


def test_register_and_login_workflows(db: None, api_client: APIClient) -> None:
    # try to register without first_name / last_name
    email = "test@example.com"
    password = FFAdminUser.objects.make_random_password()
    register_data = {
        "email": email,
        "password": password,
        "re_password": password,
    }
    register_url = reverse("api-v1:custom_auth:ffadminuser-list")
    register_response_fail = api_client.post(register_url, data=register_data)

    assert register_response_fail.status_code == status.HTTP_400_BAD_REQUEST

    # now register with full data
    register_data["first_name"] = "test"
    register_data["last_name"] = "user"
    register_response_success = api_client.post(register_url, data=register_data)
    assert register_response_success.status_code == status.HTTP_201_CREATED
    assert register_response_success.json()["key"]

    # now verify we can login with the same credentials
    new_login_data = {
        "email": email,
        "password": password,
    }
    login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")
    new_login_response = api_client.post(login_url, data=new_login_data)
    assert new_login_response.status_code == status.HTTP_200_OK
    assert new_login_response.json()["key"]

    # Oh no, we forgot our password
    reset_password_url = reverse("api-v1:custom_auth:ffadminuser-reset-password")
    reset_password_data = {"email": email}
    reset_password_response = api_client.post(
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
    reset_password_confirm_response = api_client.post(
        reset_password_confirm_url, data=reset_password_confirm_data
    )
    assert reset_password_confirm_response.status_code == status.HTTP_204_NO_CONTENT

    # now check we can login with the new details
    new_login_data = {
        "email": email,
        "password": new_password,
    }
    new_login_response = api_client.post(login_url, data=new_login_data)
    assert new_login_response.status_code == status.HTTP_200_OK
    assert new_login_response.json()["key"]


@override_settings(ALLOW_REGISTRATION_WITHOUT_INVITE=False)
def test_cannot_register_without_invite_if_disabled(
    db: None, api_client: APIClient
) -> None:
    # Given
    email = "test@example.com"
    password = FFAdminUser.objects.make_random_password()
    register_data = {
        "email": email,
        "password": password,
        "first_name": "test",
        "last_name": "register",
    }

    # When
    url = reverse("api-v1:custom_auth:ffadminuser-list")
    response = api_client.post(url, data=register_data)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@override_settings(ALLOW_REGISTRATION_WITHOUT_INVITE=False)
def test_can_register_with_invite_if_registration_disabled_without_invite(
    db: None,
    api_client: APIClient,
) -> None:
    # Given
    email = "test@example.com"
    password = FFAdminUser.objects.make_random_password()
    organisation = Organisation.objects.create(name="Test Organisation")
    register_data = {
        "email": email,
        "password": password,
        "first_name": "test",
        "last_name": "register",
    }
    Invite.objects.create(email=email, organisation=organisation)

    # When
    url = reverse("api-v1:custom_auth:ffadminuser-list")
    response = api_client.post(url, data=register_data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED


@override_settings(
    DJOSER=ChainMap(
        {"SEND_ACTIVATION_EMAIL": True, "SEND_CONFIRMATION_EMAIL": False},
        settings.DJOSER,
    )
)
def test_registration_and_login_with_user_activation_flow(
    db: None,
    api_client: APIClient,
) -> None:
    """
    Test user registration and login flow via email activation.
    By default activation flow is disabled
    """

    # Given user registration data
    email = "test@example.com"
    password = FFAdminUser.objects.make_random_password()
    register_data = {
        "email": email,
        "password": password,
        "first_name": "test",
        "last_name": "register",
    }

    # When register
    register_url = reverse("api-v1:custom_auth:ffadminuser-list")
    result = api_client.post(
        register_url, data=register_data, status_code=status.HTTP_201_CREATED
    )

    # Then success and account inactive
    assert "key" in result.data
    assert "is_active" in result.data
    assert not result.data["is_active"]

    new_user = FFAdminUser.objects.latest("id")
    assert new_user.email == register_data["email"]
    assert new_user.is_active is False

    # And login should fail as we have not activated account yet
    login_data = {
        "email": email,
        "password": password,
    }
    login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")
    failed_login_res = api_client.post(login_url, data=login_data)
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
    api_client.post(
        activate_url, data=activate_data, status_code=status.HTTP_204_NO_CONTENT
    )

    # And login success
    login_result = api_client.post(login_url, data=login_data)
    assert login_result.status_code == status.HTTP_200_OK
    assert "key" in login_result.data


def test_login_workflow_with_mfa_enabled(
    db: None,
    api_client: APIClient,
) -> None:
    email = "test@example.com"
    password = FFAdminUser.objects.make_random_password()
    register_data = {
        "email": email,
        "password": password,
        "re_password": password,
        "first_name": "test",
        "last_name": "user",
    }
    register_url = reverse("api-v1:custom_auth:ffadminuser-list")
    register_response = api_client.post(register_url, data=register_data)
    assert register_response.status_code == status.HTTP_201_CREATED
    key = register_response.json()["key"]

    # authenticate the test client
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {key}")

    # create an MFA method
    create_mfa_method_url = reverse(
        "api-v1:custom_auth:mfa-activate", kwargs={"method": "app"}
    )
    create_mfa_response = api_client.post(create_mfa_method_url)
    assert create_mfa_response.status_code == status.HTTP_200_OK
    secret = create_mfa_response.json()["secret"]

    # confirm the MFA method
    totp = pyotp.TOTP(secret)
    confirm_mfa_data = {"code": totp.now()}
    confirm_mfa_method_url = reverse(
        "api-v1:custom_auth:mfa-activate-confirm", kwargs={"method": "app"}
    )
    confirm_mfa_method_response = api_client.post(
        confirm_mfa_method_url, data=confirm_mfa_data
    )
    assert confirm_mfa_method_response.status_code == status.HTTP_200_OK
    backup_codes = confirm_mfa_method_response.json()["backup_codes"]

    # now login should return an ephemeral token rather than a token
    login_data = {"email": email, "password": password}
    api_client.logout()
    login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")
    login_response = api_client.post(login_url, data=login_data)
    assert login_response.status_code == status.HTTP_200_OK
    ephemeral_token = login_response.json()["ephemeral_token"]

    # now we can confirm the login
    confirm_login_data = {"ephemeral_token": ephemeral_token, "code": totp.now()}
    login_confirm_url = reverse("api-v1:custom_auth:mfa-authtoken-login-code")
    login_confirm_response = api_client.post(login_confirm_url, data=confirm_login_data)
    assert login_confirm_response.status_code == status.HTTP_200_OK
    key = login_confirm_response.json()["key"]

    # Login with backup code should also work
    api_client.logout()
    login_response = api_client.post(login_url, data=login_data)
    assert login_response.status_code == status.HTTP_200_OK
    ephemeral_token = login_response.json()["ephemeral_token"]
    confirm_login_data = {
        "ephemeral_token": ephemeral_token,
        "code": backup_codes[0],
    }
    login_confirm_response = api_client.post(login_confirm_url, data=confirm_login_data)
    assert login_confirm_response.status_code == status.HTTP_200_OK
    key = login_confirm_response.json()["key"]

    # and verify that we can use the token to access the API
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {key}")
    current_user_url = reverse("api-v1:custom_auth:ffadminuser-me")
    current_user_response = api_client.get(current_user_url)
    assert current_user_response.status_code == status.HTTP_200_OK
    assert current_user_response.json()["email"] == email


def test_throttle_login_workflows(
    api_client: APIClient,
    db: None,
    reset_cache: None,
    mocker: MockerFixture,
) -> None:
    # verify that a throttle rate exists already then set it
    # to something easier to reliably test
    assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["login"]
    mocker.patch(
        "rest_framework.throttling.ScopedRateThrottle.get_rate", return_value="1/minute"
    )
    email = "test@example.com"
    password = FFAdminUser.objects.make_random_password()
    register_data = {
        "email": email,
        "password": password,
        "re_password": password,
        "first_name": "test",
        "last_name": "user",
    }
    register_url = reverse("api-v1:custom_auth:ffadminuser-list")
    register_response = api_client.post(register_url, data=register_data)
    assert register_response.status_code == status.HTTP_201_CREATED
    assert register_response.json()["key"]

    # verify we can login with credentials
    login_data = {
        "email": email,
        "password": password,
    }
    login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")
    login_response = api_client.post(login_url, data=login_data)
    assert login_response.status_code == status.HTTP_200_OK
    assert login_response.json()["key"]

    # try login in again, should deny, current limit 1 per second
    login_response = api_client.post(login_url, data=login_data)
    assert login_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_throttle_signup(
    api_client: APIClient,
    user_password: str,
    db: None,
    reset_cache: None,
    mocker: MockerFixture,
) -> None:
    # verify that a throttle rate exists already then set it
    # to something easier to reliably test
    assert settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["signup"]
    mocker.patch(
        "rest_framework.throttling.ScopedRateThrottle.get_rate", return_value="1/minute"
    )
    # Next, let's hit signup for the first time
    register_data = {
        "email": "user_1_email@mail.com",
        "password": user_password,
        "re_password": user_password,
        "first_name": "user_1",
        "last_name": "user_1_last_name",
    }
    register_url = reverse("api-v1:custom_auth:ffadminuser-list")
    register_response = api_client.post(register_url, data=register_data)

    # Assert that signup worked
    assert register_response.status_code == status.HTTP_201_CREATED
    assert register_response.json()["key"]

    # Now, let's signup again
    register_url = reverse("api-v1:custom_auth:ffadminuser-list")
    response = api_client.post(register_url, data=register_data)

    # Assert that we got throttled
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


def test_get_user_is_not_throttled(
    admin_client: APIClient, reset_cache: None, mocker: MockerFixture
):
    # Given
    mocker.patch(
        "rest_framework.throttling.ScopedRateThrottle.get_rate", return_value="1/minute"
    )
    url = reverse("api-v1:custom_auth:ffadminuser-me")
    # When
    for _ in range(2):
        response = admin_client.get(url)
        # Then
        assert response.status_code == status.HTTP_200_OK


def test_delete_token(test_user, auth_token):
    # Given
    url = reverse("api-v1:custom_auth:delete-token")
    client = APIClient(HTTP_AUTHORIZATION=f"Token {auth_token.key}")

    # When
    response = client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # and - if we try to delete the token again(i.e: access anything that uses is_authenticated)
    # we should will get 401
    assert client.delete(url).status_code == status.HTTP_401_UNAUTHORIZED


def test_register_with_sign_up_type(client, db, settings):
    # Given
    password = FFAdminUser.objects.make_random_password()
    sign_up_type = "NO_INVITE"
    email = "test@example.com"
    register_data = {
        "email": email,
        "password": password,
        "re_password": password,
        "first_name": "test",
        "last_name": "tester",
        "sign_up_type": sign_up_type,
    }

    # When
    response = client.post(
        reverse("api-v1:custom_auth:ffadminuser-list"),
        data=json.dumps(register_data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert response_json["sign_up_type"] == sign_up_type

    assert FFAdminUser.objects.filter(email=email, sign_up_type=sign_up_type).exists()

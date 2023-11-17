import json

import pytest
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.urls import reverse
from djoser import utils
from djoser.email import PasswordResetEmail
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation
from users.models import FFAdminUser


@pytest.mark.django_db
def test_delete_user():
    def delete_user(
        user: FFAdminUser, password: str, delete_orphan_organisations: bool = True
    ):
        client = APIClient()
        client.force_authenticate(user)
        data = {
            "current_password": password,
            "delete_orphan_organisations": delete_orphan_organisations,
        }
        url = "/api/v1/auth/users/me/"
        return client.delete(
            url, data=json.dumps(data), content_type="application/json"
        )

    # create a couple of users
    email1 = "test1@example.com"
    email2 = "test2@example.com"
    email3 = "test3@example.com"
    password = "password"
    user1 = FFAdminUser.objects.create_user(email=email1, password=password)
    user2 = FFAdminUser.objects.create_user(email=email2, password=password)
    user3 = FFAdminUser.objects.create_user(email=email3, password=password)

    # create some organisations
    org1 = Organisation.objects.create(name="org1")
    org2 = Organisation.objects.create(name="org2")
    org3 = Organisation.objects.create(name="org3")

    # add the test user 1 to all the organizations (cannot use Organisation.users reverse accessor)
    user1.organisations.add(org1, org2, org3)

    # add test user 2 to org2 and user 3 to to org1
    user2.organisations.add(org2)
    user3.organisations.add(org1)

    # Configuration: org1: [user1, user3], org2: [user1, user2], org3: [user1]

    # Delete user2
    response = delete_user(user2, password)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FFAdminUser.objects.filter(email=email2).exists()

    # All organisations remain since user 2 has org2 as only organization and it has 2 users
    assert Organisation.objects.filter(name="org3").count() == 1
    assert Organisation.objects.filter(name="org1").count() == 1
    assert Organisation.objects.filter(name="org2").count() == 1

    # Delete user1
    response = delete_user(user1, password)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FFAdminUser.objects.filter(email=email1).exists()

    # organization org3 and org2 are deleted since its only user is user1
    assert Organisation.objects.filter(name="org3").count() == 0
    assert Organisation.objects.filter(name="org2").count() == 0

    # org1 remain
    assert Organisation.objects.filter(name="org1").count() == 1

    # user3 remain
    assert FFAdminUser.objects.filter(email=email3).exists()

    # Delete user3
    response = delete_user(user3, password, False)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FFAdminUser.objects.filter(email=email3).exists()
    assert Organisation.objects.filter(name="org1").count() == 1


@pytest.mark.django_db
def test_change_email_address_api(mocker):
    # Given
    mocked_task = mocker.patch("users.signals.send_email_changed_notification_email")
    # create an user
    old_email = "test_user@test.com"
    first_name = "firstname"
    user = FFAdminUser.objects.create_user(
        username="test_user",
        email=old_email,
        first_name=first_name,
        last_name="user",
        password="password",
    )

    client = APIClient()
    client.force_authenticate(user)
    new_email = "test_user1@test.com"
    data = {"new_email": new_email, "current_password": "password"}

    url = reverse("api-v1:custom_auth:ffadminuser-set-username")

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert user.email == new_email

    args, kwargs = mocked_task.delay.call_args

    assert len(args) == 0
    assert len(kwargs) == 1
    assert kwargs["args"] == (first_name, settings.DEFAULT_FROM_EMAIL, old_email)


@pytest.mark.django_db
def test_send_reset_password_emails_rate_limit(settings, client, test_user):
    # Given
    settings.MAX_PASSWORD_RESET_EMAILS = 2
    settings.PASSWORD_RESET_EMAIL_COOLDOWN = 60

    url = reverse("api-v1:custom_auth:ffadminuser-reset-password")
    data = {"email": test_user.email}

    # When
    for _ in range(5):
        response = client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    # Then - we should only have two emails
    assert len(mail.outbox) == 2
    isinstance(mail.outbox[0], PasswordResetEmail)
    isinstance(mail.outbox[1], PasswordResetEmail)

    # clear the outbox
    mail.outbox.clear()

    # Next, let's reduce the cooldown to 1 second and try again
    settings.PASSWORD_RESET_EMAIL_COOLDOWN = 0.001
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then - we should receive another email
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert len(mail.outbox) == 1
    isinstance(mail.outbox[0], PasswordResetEmail)


@pytest.mark.django_db
def test_send_reset_password_emails_rate_limit_resets_after_password_reset(
    settings, client, test_user
):
    # Given
    settings.MAX_PASSWORD_RESET_EMAILS = 2
    settings.PASSWORD_RESET_EMAIL_COOLDOWN = 60 * 60 * 24

    url = reverse("api-v1:custom_auth:ffadminuser-reset-password")
    data = {"email": test_user.email}

    # First, let's hit the limit of emails we can send
    for _ in range(5):
        response = client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    # Then - we should only have two emails
    assert len(mail.outbox) == 2
    mail.outbox.clear()

    # Next, let's reset the password
    reset_password_data = {
        "new_password": "new_password",
        "re_new_password": "new_password",
        "uid": utils.encode_uid(test_user.pk),
        "token": default_token_generator.make_token(test_user),
    }
    reset_password_confirm_url = reverse(
        "api-v1:custom_auth:ffadminuser-reset-password-confirm"
    )
    response = client.post(
        reset_password_confirm_url,
        data=json.dumps(reset_password_data),
        content_type="application/json",
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Finally, let's try to send another email
    client.post(url, data=json.dumps(data), content_type="application/json")

    # Then - we should receive another email
    assert len(mail.outbox) == 1

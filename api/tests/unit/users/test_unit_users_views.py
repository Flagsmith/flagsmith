import json

import pytest
from django.conf import settings
from rest_framework import status
from rest_framework.test import APIClient

from users.models import FFAdminUser


@pytest.mark.django_db
def test_change_email_address_api(mocker):
    # Given
    mocked_send_mail = mocker.patch("users.tasks.send_mail")
    # create an user
    user = FFAdminUser.objects.create(
        username="test_user",
        email="test_user@test.com",
        first_name="test",
        last_name="user",
    )
    user.set_password("password")

    client = APIClient()
    client.force_authenticate(user)
    old_email = "test_user@test.com"
    new_email = "test_user1@test.com"
    data = {"new_email": new_email, "current_password": "password"}

    url = "/api/v1/auth/users/set_email/"

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert user.email == new_email

    args, kwargs = mocked_send_mail.call_args

    assert len(args) == 0
    assert len(kwargs) == 5
    assert kwargs["subject"] == "Your Flagsmith email address has been changed"
    assert kwargs["from_email"] == settings.DEFAULT_FROM_EMAIL
    assert kwargs["recipient_list"] == [old_email]
    assert kwargs["fail_silently"] is True

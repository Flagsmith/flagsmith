import json

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import FFAdminUser


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

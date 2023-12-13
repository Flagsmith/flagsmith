import os
from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper

from custom_auth.models import UserPasswordResetRequest
from custom_auth.tasks import clean_up_user_password_reset_request
from task_processor.management.commands.runprocessor import (
    Command as RunProcessorCommand,
)
from task_processor.models import RecurringTask
from users.models import FFAdminUser


def test_clean_up_user_password_reset_request(
    settings: SettingsWrapper, test_user: FFAdminUser, freezer
):
    # Given
    settings.PASSWORD_RESET_EMAIL_COOLDOWN = 10
    now = timezone.now()

    # A user password reset request should be deleted
    UserPasswordResetRequest.objects.create(user=test_user)

    freezer.move_to(now + timedelta(seconds=11))

    # A user password reset request should not be deleted
    new_user_password_reset_request = UserPasswordResetRequest.objects.create(
        user=test_user
    )
    # When
    clean_up_user_password_reset_request()

    # Then
    assert UserPasswordResetRequest.objects.count() == 1
    assert (
        UserPasswordResetRequest.objects.first().id
        == new_user_password_reset_request.id
    )


@mock.patch.dict(os.environ, {})
@pytest.mark.django_db
def test_clean_up_user_password_reset_request_is_installed_correctly():
    # When
    # Initialising the command should save the task to the database
    RunProcessorCommand()

    # Then
    assert (
        RecurringTask.objects.filter(
            task_identifier=f"tasks.{clean_up_user_password_reset_request.__name__}"
        ).exists()
        is True
    )

import json

import pytest
from django.test import Client
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_django.fixtures import SettingsWrapper

from app.utils import get_version_info
from users.models import FFAdminUser


def test_get_version_info(fs: FakeFilesystem, db: None) -> None:
    # Given
    expected_manifest_contents = {
        ".": "2.66.2",
    }

    fs.create_file("./ENTERPRISE_VERSION")
    fs.create_file(".versions.json", contents=json.dumps(expected_manifest_contents))
    fs.create_file("./CI_COMMIT_SHA", contents="some_sha")

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "some_sha",
        "image_tag": "2.66.2",
        "has_email_provider": False,
        "is_enterprise": True,
        "is_saas": False,
        "package_versions": {".": "2.66.2"},
        "self_hosted_data": {
            "has_users": False,
            "has_logins": False,
            "is_bootstrapped": False,
        },
    }


def test_get_version_info_self_hosted_data_is_bootstrapped(
    fs: FakeFilesystem, db: None, settings: SettingsWrapper, user_one: FFAdminUser
) -> None:
    # Given
    fs.create_file("./ENTERPRISE_VERSION")
    settings.ALLOW_ADMIN_INITIATION_VIA_CLI = True
    settings.ADMIN_EMAIL = user_one.email

    # When
    result = get_version_info()

    # Then
    assert result["self_hosted_data"] == {
        "is_bootstrapped": True,
        "has_logins": False,
        "has_users": True,
    }


def test_get_version_info_self_hosted_data_users_and_login(
    fs: FakeFilesystem, db: None, settings: SettingsWrapper, client: Client
) -> None:
    # Given
    fs.create_file("./ENTERPRISE_VERSION")

    result = get_version_info()

    # Let's make sure everything is
    # as expected before we create the users
    assert result["self_hosted_data"] == {
        "is_bootstrapped": False,
        "has_logins": False,
        "has_users": False,
    }
    # When
    user = FFAdminUser.objects.create(email="user_two@test.com")

    client.force_login(user)
    result = get_version_info()

    # Then
    result["self_hosted_data"] == {
        "is_bootstrapped": False,
        "has_logins": True,
        "has_users": True,
    }


def test_get_version_info_with_missing_files(fs: FakeFilesystem, db: None) -> None:
    # Given
    fs.create_file("./ENTERPRISE_VERSION")

    # When
    result = get_version_info()
    # Then
    assert result == {
        "ci_commit_sha": "unknown",
        "image_tag": "unknown",
        "has_email_provider": False,
        "is_enterprise": True,
        "is_saas": False,
        "self_hosted_data": {
            "has_users": False,
            "has_logins": False,
            "is_bootstrapped": False,
        },
    }


EMAIL_BACKENDS_AND_SETTINGS = [
    ("django.core.mail.backends.smtp.EmailBackend", "EMAIL_HOST_USER"),
    ("django_ses.SESBackend", "AWS_SES_REGION_ENDPOINT"),
    ("sgbackend.SendGridBackend", "SENDGRID_API_KEY"),
]


@pytest.mark.parametrize(
    "email_backend,expected_setting_name",
    EMAIL_BACKENDS_AND_SETTINGS,
)
def test_get_version_info__email_config_enabled__return_expected(
    settings: SettingsWrapper, email_backend: str, expected_setting_name: str, db: None
) -> None:
    # Given
    settings.EMAIL_BACKEND = email_backend
    setattr(settings, expected_setting_name, "value")

    # When
    result = get_version_info()

    # Then
    assert result["has_email_provider"] is True


@pytest.mark.parametrize(
    "email_backend,expected_setting_name",
    [
        (None, None),
        *EMAIL_BACKENDS_AND_SETTINGS,
    ],
)
def test_get_version_info__email_config_disabled__return_expected(
    settings: SettingsWrapper,
    email_backend: str | None,
    expected_setting_name: str | None,
    db: None,
) -> None:
    # Given
    settings.EMAIL_BACKEND = email_backend
    if expected_setting_name:
        setattr(settings, expected_setting_name, None)

    # When
    result = get_version_info()

    # Then
    assert result["has_email_provider"] is False

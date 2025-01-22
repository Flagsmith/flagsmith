import json
from typing import Generator

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from app.utils import get_version_info


@pytest.fixture(autouse=True)
def clear_get_version_info_cache() -> Generator[None, None, None]:
    yield
    get_version_info.cache_clear()


def test_get_version_info(
    mocker: MockerFixture,
    fs: FakeFilesystem,
) -> None:
    # Given
    fs.create_file("./ENTERPRISE_VERSION")

    manifest_mocked_file = {
        ".": "2.66.2",
    }
    mock_get_file_contents = mocker.patch("app.utils._get_file_contents")
    mock_get_file_contents.side_effect = (json.dumps(manifest_mocked_file), "some_sha")

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
    }


def test_get_version_info_with_missing_files(
    mocker: MockerFixture,
    fs: FakeFilesystem,
) -> None:
    # Given
    fs.create_file("./ENTERPRISE_VERSION")

    mock_open = mocker.patch("app.utils.open")
    mock_open.side_effect = FileNotFoundError

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "unknown",
        "image_tag": "unknown",
        "has_email_provider": False,
        "is_enterprise": True,
        "is_saas": False,
    }


def test_get_version_info_with_email_config_smtp(settings: SettingsWrapper) -> None:
    # Given
    settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    settings.EMAIL_HOST_USER = "user"

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "unknown",
        "image_tag": "unknown",
        "has_email_provider": True,
        "is_enterprise": False,
        "is_saas": False,
    }


def test_get_version_info_with_email_config_sendgrid(settings: SettingsWrapper) -> None:
    # Given
    settings.EMAIL_BACKEND = "sgbackend.SendGridBackend"
    settings.SENDGRID_API_KEY = "key"

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "unknown",
        "image_tag": "unknown",
        "has_email_provider": True,
        "is_enterprise": False,
        "is_saas": False,
    }


def test_get_version_info_with_email_config_ses(settings: SettingsWrapper) -> None:
    # Given
    settings.EMAIL_BACKEND = "django_ses.SESBackend"
    settings.AWS_SES_REGION_ENDPOINT = "endpoint"

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "unknown",
        "image_tag": "unknown",
        "has_email_provider": True,
        "is_enterprise": False,
        "is_saas": False,
    }


@pytest.mark.parametrize(
    "email_backend,expected_empty_setting_name",
    [
        (None, None),
        ("django.core.mail.backends.smtp.EmailBackend", "EMAIL_HOST_USER"),
        ("django_ses.SESBackend", "AWS_SES_REGION_ENDPOINT"),
        ("sgbackend.SendGridBackend", "SENDGRID_API_KEY"),
    ],
)
def test_get_version_info_without_email_config(
    settings: SettingsWrapper,
    email_backend: str | None,
    expected_empty_setting_name: str | None,
) -> None:
    # Given
    settings.EMAIL_BACKEND = email_backend
    if expected_empty_setting_name:
        setattr(settings, expected_empty_setting_name, None)

    # When
    result = get_version_info()

    # Then
    assert result["has_email_provider"] is False

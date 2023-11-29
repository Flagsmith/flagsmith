import typing

import pytest
from core.helpers import get_current_site_url
from django.contrib.sites.models import Site

if typing.TYPE_CHECKING:
    from pytest_django.fixtures import SettingsWrapper
    from pytest_mock import MockerFixture

pytestmark = pytest.mark.django_db


def test_get_current_site_url_returns_correct_url_if_site_exists(
    settings: "SettingsWrapper",
) -> None:
    # Given
    expected_domain = "some-testing-url.com"
    site = Site.objects.create(name="test_site", domain=expected_domain)
    settings.SITE_ID = site.id

    # When
    url = get_current_site_url()

    # Then
    assert url == f"https://{expected_domain}"


def test_get_current_site_url_uses_default_url_if_site_does_not_exists(
    settings: "SettingsWrapper",
) -> None:
    # Given
    expected_domain = "some-testing-url.com"
    settings.DEFAULT_DOMAIN = expected_domain
    settings.SITE_ID = None

    # When
    url = get_current_site_url()

    # Then
    assert url == f"https://{expected_domain}"


def test_get_current_site__domain_override__with_site__return_expected(
    settings: "SettingsWrapper",
) -> None:
    # Given
    site = Site.objects.create(name="test_site", domain="should-not-be-used.com")
    settings.SITE_ID = site.id

    expected_domain = "some-testing-url.com"
    settings.DOMAIN_OVERRIDE = expected_domain

    # When
    url = get_current_site_url()

    # Then
    assert url == f"https://{expected_domain}"


def test_get_current_site__domain_override__no_site__return_expected(
    settings: "SettingsWrapper",
) -> None:
    # Given
    settings.SITE_ID = None

    expected_domain = "some-testing-url.com"
    settings.DOMAIN_OVERRIDE = expected_domain

    # When
    url = get_current_site_url()

    # Then
    assert url == f"https://{expected_domain}"


def test_get_current_site__insecure_request__return_expected(
    settings: "SettingsWrapper",
    mocker: "MockerFixture",
) -> None:
    # Given
    expected_domain = "some-testing-url.com"
    settings.DOMAIN_OVERRIDE = expected_domain

    expected_request = mocker.Mock(scheme="http")

    # When
    url = get_current_site_url(expected_request)

    # Then
    assert url == f"http://{expected_domain}"


@pytest.mark.parametrize(
    "expected_domain", ["localhost", "127.0.0.1", "localhost:4219"]
)
def test_get_current_site__localhost__return_expected(
    settings: "SettingsWrapper",
    expected_domain: str,
) -> None:
    # Given
    settings.DOMAIN_OVERRIDE = expected_domain

    # When
    url = get_current_site_url()

    # Then
    assert url == f"http://{expected_domain}"

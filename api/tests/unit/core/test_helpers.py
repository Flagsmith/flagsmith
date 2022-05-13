from core.helpers import get_current_site_url
from django.contrib.sites.models import Site


def test_get_current_site_url_returns_correct_url_if_site_exists(settings, db):
    # Given
    domain = "some-testing-url.com"
    site = Site.objects.create(name="test_site", domain=domain)
    settings.SITE_ID = site.id

    # When
    url = get_current_site_url()

    # Then
    assert url == f"https://{domain}"


def test_get_current_site_url_uses_default_url_if_site_does_not_exists(settings, db):
    # Given
    domain = "some-testing-url.com"
    settings.SITE_ID = None

    # When
    url = get_current_site_url(default_domain=domain)

    # Then
    assert url == f"https://{domain}"

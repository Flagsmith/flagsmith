from importlib import reload

import pytest
from django.urls import clear_url_caches


def reload_onboarding_urls() -> None:
    import api.urls.v1 as v1_urls
    import app.urls.api as root_urls
    import onboarding.urls as onboarding_urls

    reload(onboarding_urls)
    reload(v1_urls)
    reload(root_urls)

    clear_url_caches()


@pytest.fixture()
def oss_mode() -> None:
    reload_onboarding_urls()


@pytest.fixture()
def saas_mode(saas_mode: None) -> None:
    reload_onboarding_urls()

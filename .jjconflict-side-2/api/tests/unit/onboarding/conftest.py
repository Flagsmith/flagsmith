from importlib import reload

import pytest
from django.urls import clear_url_caches
from pytest_mock import MockerFixture


def reload_onboarding_urls() -> None:
    import api.urls.v1 as v1_urls
    import app.urls as root_urls
    import onboarding.urls as onboarding_urls

    reload(onboarding_urls)
    reload(v1_urls)
    reload(root_urls)

    clear_url_caches()


@pytest.fixture()
def is_oss(mocker: MockerFixture) -> None:
    mocker.patch("common.core.utils.is_oss", return_value=True)
    reload_onboarding_urls()


@pytest.fixture()
def is_saas(mocker: MockerFixture) -> None:
    mocker.patch("common.core.utils.is_saas", return_value=True)
    reload_onboarding_urls()

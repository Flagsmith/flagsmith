import pytest


@pytest.fixture()
def sse_enabled_settings(settings):
    settings.SSE_SERVER_BASE_URL = "http://localhost:8000"
    settings.SSE_AUTHENTICATION_TOKEN = "test-token"
    return settings


@pytest.fixture()
def sse_disabled_settings(settings):
    settings.SSE_SERVER_BASE_URL = ""
    settings.SSE_AUTHENTICATION_TOKEN = ""
    return settings

import pytest

from integrations.lead_tracking.pipedrive.client import PipedriveAPIClient


@pytest.fixture()
def pipedrive_api_token():  # type: ignore[no-untyped-def]
    return "some-token"


@pytest.fixture()
def pipedrive_base_url():  # type: ignore[no-untyped-def]
    return "https://org.pipedrive.com/api/v1"


@pytest.fixture()
def pipedrive_api_client(pipedrive_api_token, pipedrive_base_url):  # type: ignore[no-untyped-def]
    return PipedriveAPIClient(
        api_token=pipedrive_api_token, base_url=pipedrive_base_url
    )

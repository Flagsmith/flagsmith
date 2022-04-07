import pytest


@pytest.fixture()
def forwarder_mocked_migrator(mocker):
    return mocker.patch(
        "edge_api.identities.edge_request_forwarder.IdentityMigrator",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture()
def forward_enable_settings(settings):
    settings.EDGE_API_URL = "http//localhost"
    settings.EDGE_REQUEST_SIGNING_KEY = "test_key"
    return settings

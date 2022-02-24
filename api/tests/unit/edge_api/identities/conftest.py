import pytest


@pytest.fixture()
def forwarder_dynamo_wrapper(mocker):
    return mocker.patch("edge_api.identities.forwarder.DynamoIdentityWrapper")


@pytest.fixture()
def forward_enable_settings(settings):
    settings.EDGE_API_URL = "http//localhost"
    settings.EDGE_REQUEST_SIGNING_KEY = "test_key"
    return settings

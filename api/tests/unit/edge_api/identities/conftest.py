import pytest


@pytest.fixture()
def forwarder_dynamo_wrapper(mocker):
    return mocker.patch("edge_api.identities.forwarder.DynamoIdentityWrapper")

import pytest


@pytest.fixture()
def edge_identity_dynamo_wrapper_mock(mocker):
    return mocker.patch(
        "edge_api.identities.models.EdgeIdentity.dynamo_wrapper",
    )

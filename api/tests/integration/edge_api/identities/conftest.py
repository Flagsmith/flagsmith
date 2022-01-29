import pytest


@pytest.fixture()
def dynamo_wrapper_mock(mocker):
    return mocker.patch(
        "environments.identities.models.Identity.dynamo_wrapper",
    )

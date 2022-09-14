import pytest


@pytest.fixture()
def dynamo_wrapper_mock(mocker):
    return mocker.patch(
        "environments.identities.models.Identity.dynamo_wrapper",
    )


@pytest.fixture()
def webhook_mock(mocker):
    return mocker.patch(
        "edge_api.identities.serializers.call_environment_webhook_for_feature_state_change"
    )

import pytest


@pytest.fixture()
def webhook_mock(mocker):
    return mocker.patch(
        "edge_api.identities.serializers.call_environment_webhook_for_feature_state_change"
    )

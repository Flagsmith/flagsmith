from string import Template

import pytest
from django.urls import reverse


@pytest.fixture()
def webhook_mock(mocker):
    return mocker.patch(
        "edge_api.identities.serializers.call_environment_webhook_for_feature_state_change"
    )


@pytest.fixture()
def featurestates_urls(environment_api_key: str) -> dict[str, Template]:
    return {
        "clone-flag-states-from": Template(
            reverse(
                "api-v1:environments:edge-identity-featurestates-clone-flag-states-from",
                args=(environment_api_key, "$identity_uuid"),
            )
        ),
        "all": Template(
            reverse(
                "api-v1:environments:edge-identity-featurestates-all",
                args=(environment_api_key, "$identity_uuid"),
            )
        ),
    }

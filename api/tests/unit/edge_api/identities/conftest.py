import pytest

from edge_api.identities.models import EdgeIdentity
from environments.models import Environment
from features.models import Feature


@pytest.fixture()
def forwarder_mocked_migrator(mocker):
    return mocker.patch(
        "edge_api.identities.edge_request_forwarder.IdentityMigrator",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture()
def forwarder_mocked_requests(mocker):
    return mocker.patch(
        "edge_api.identities.edge_request_forwarder.requests",
        autospec=True,
        spec_set=True,
    )


@pytest.fixture()
def forward_enable_settings(settings):
    settings.EDGE_API_URL = "http//localhost"
    settings.EDGE_REQUEST_SIGNING_KEY = "test_key"
    return settings


@pytest.fixture()
def identity_document_without_fs(environment):
    return {
        "composite_key": f"{environment.api_key}_user_1_test",
        "identity_traits": [],
        "identity_features": [],
        "identifier": "user_1_test",
        "created_date": "2021-09-21T10:12:42.230257+00:00",
        "environment_api_key": environment.api_key,
        "identity_uuid": "59efa2a7-6a45-46d6-b953-a7073a90eacf",
        "django_id": None,
    }


@pytest.fixture()
def edge_identity_model(identity_document_without_fs):
    return EdgeIdentity.from_identity_document(identity_document_without_fs)


@pytest.fixture()
def edge_identity_override_document(
    environment: Environment,
    feature: Feature,
    edge_identity_model: EdgeIdentity,
) -> dict:
    return {
        "environment_id": environment.id,
        "document_key": f"identity_override:{feature.id}:{edge_identity_model.identity_uuid}",
        "environment_api_key": environment.api_key,
        "identifier": edge_identity_model.identifier,
        "identity_uuid": edge_identity_model.identity_uuid,
        "feature_state": {
            "django_id": None,
            "enabled": True,
            "feature": {"id": feature.id, "name": feature.name, "type": feature.type},
            "featurestate_uuid": "a7495917-ee57-41d1-a64e-e0697dbc57fb",
            "feature_segment": None,
            "feature_state_value": None,
            "multivariate_feature_state_values": [],
        },
    }


@pytest.fixture()
def identity_document_2(environment):
    return {
        "composite_key": f"{environment.api_key}_user_2_test",
        "identity_traits": [],
        "identity_features": [],
        "identifier": "user_2_test",
        "created_date": "2021-09-21T10:12:42.230257+00:00",
        "environment_api_key": environment.api_key,
        "identity_uuid": "c0ed9184-2832-42dc-a132-5eb45afd1181",
        "django_id": None,
    }


@pytest.fixture()
def edge_identity_model_2(identity_document_2):
    return EdgeIdentity.from_identity_document(identity_document_2)


@pytest.fixture()
def edge_identity_override_document_2(
    environment: Environment,
    feature: Feature,
    edge_identity_model_2: EdgeIdentity,
) -> dict:
    return {
        "environment_id": environment.id,
        "document_key": f"identity_override:{feature.id}:{edge_identity_model_2.identity_uuid}",
        "environment_api_key": environment.api_key,
        "identifier": edge_identity_model_2.identifier,
        "identity_uuid": edge_identity_model_2.identity_uuid,
        "feature_state": {
            "django_id": None,
            "enabled": True,
            "feature": {"id": feature.id, "name": feature.name, "type": feature.type},
            "featurestate_uuid": "a7495917-ee57-41d1-a64e-e0697dbc57fb",
            "feature_segment": None,
            "feature_state_value": None,
            "multivariate_feature_state_values": [],
        },
    }

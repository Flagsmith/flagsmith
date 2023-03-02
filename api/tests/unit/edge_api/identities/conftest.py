import pytest

from edge_api.identities.models import EdgeIdentity


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

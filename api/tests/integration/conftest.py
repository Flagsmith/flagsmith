import json
import uuid

import pytest
from django.test import Client as DjangoClient
from django.urls import reverse
from rest_framework.test import APIClient

from app.utils import create_hash


@pytest.fixture()
def mv_option_value():
    return "test_mv_value"


@pytest.fixture()
def django_client():
    return DjangoClient()


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture()
def organisation(admin_client):
    organisation_data = {"name": "Test org"}
    url = reverse("api-v1:organisations:organisation-list")
    response = admin_client.post(url, data=organisation_data)
    return response.json()["id"]


@pytest.fixture()
def project(admin_client, organisation):
    project_data = {"name": "Test Project", "organisation": organisation}
    url = reverse("api-v1:projects:project-list")
    response = admin_client.post(url, data=project_data)
    return response.json()["id"]


@pytest.fixture()
def dynamo_enabled_project(admin_client, organisation):
    project_data = {
        "name": "Test Project",
        "organisation": organisation,
        "enable_dynamo_db": True,
    }
    url = reverse("api-v1:projects:project-list")
    response = admin_client.post(url, data=project_data)
    return response.json()["id"]


@pytest.fixture()
def environment_api_key():
    return create_hash()


@pytest.fixture()
def environment(admin_client, project, environment_api_key) -> int:
    environment_data = {
        "name": "Test Environment",
        "api_key": environment_api_key,
        "project": project,
        "minimum_change_request_approvals": 1,
    }
    url = reverse("api-v1:environments:environment-list")

    response = admin_client.post(url, data=environment_data)
    return response.json()["id"]


@pytest.fixture()
def dynamo_enabled_environment(
    admin_client, dynamo_enabled_project, environment_api_key
) -> int:
    environment_data = {
        "name": "Test Environment",
        "api_key": environment_api_key,
        "project": dynamo_enabled_project,
    }
    url = reverse("api-v1:environments:environment-list")

    response = admin_client.post(url, data=environment_data)
    return response.json()["id"]


@pytest.fixture()
def identity_identifier():
    return uuid.uuid4()


@pytest.fixture()
def identity(admin_client, identity_identifier, environment, environment_api_key):
    identity_data = {"identifier": identity_identifier}
    url = reverse(
        "api-v1:environments:environment-identities-list", args=[environment_api_key]
    )
    response = admin_client.post(url, data=identity_data)
    return response.json()["id"]


@pytest.fixture()
def sdk_client(environment_api_key):
    client = APIClient()
    client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_api_key)
    return client


@pytest.fixture()
def default_feature_value():
    return "default_value"


@pytest.fixture()
def feature(admin_client, project, default_feature_value):
    data = {
        "name": "test feature",
        "initial_value": default_feature_value,
        "project": project,
    }
    url = reverse("api-v1:projects:project-features-list", args=[project])

    response = admin_client.post(url, data=data)
    return response.json()["id"]


@pytest.fixture()
def mv_option(admin_client, project, mv_option_value):
    data = {
        "name": "test_feature_mv",
        "default_enabled": True,
        "multivariate_options": [{"type": "unicode", "string_value": mv_option_value}],
    }
    url = reverse("api-v1:projects:project-features-list", args=[project])

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    response_json = response.json()
    return response_json["multivariate_options"][0]["id"]


@pytest.fixture()
def segment(admin_client, project):
    url = reverse("api-v1:projects:project-segments-list", args=[project])
    data = {
        "name": "Test Segment",
        "project": project,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    return response.json()["id"]


@pytest.fixture()
def feature_segment(admin_client, segment, feature, environment):
    data = {
        "feature": feature,
        "segment": segment,
        "environment": environment,
    }
    url = reverse("api-v1:features:feature-segment-list")

    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    return response.json()["id"]


@pytest.fixture()
def identity_document(environment_api_key, feature):
    _environment_feature_state_1_document = {
        "featurestate_uuid": "ad71c644-71df-4e83-9cb5-cd2cd0160200",
        "multivariate_feature_state_values": [],
        "feature_state_value": "feature_1_value",
        "id": 1,
        "feature": {
            "name": "feature_1",
            "type": "STANDARD",
            "id": feature,
        },
        "enabled": False,
    }
    _environment_feature_state_2_document = {
        "featurestate_uuid": "c6ec4de7-11a7-47c2-abc9-0d7bf0fc90e9",
        "multivariate_feature_state_values": [],
        "id": 1,
        "feature_state_value": "2.3",
        "feature": {
            "name": "feature_2",
            "type": "STANDARD",
            "id": 200,
        },
        "enabled": True,
    }
    _mv_feature_state_document = {
        "featurestate_uuid": "4a8fbe06-d4cd-4686-a184-d924844bb421",
        "multivariate_feature_state_values": [
            {
                "percentage_allocation": 50,
                "multivariate_feature_option": {"value": "50_percent"},
                "id": 1,
            },
            {
                "percentage_allocation": 50,
                "multivariate_feature_option": {"value": "other_50_percent"},
                "id": 2,
            },
        ],
        "feature_state_value": None,
        "id": 1,
        "feature": {
            "name": "multivariate_feature",
            "type": "MULTIVARIATE",
            "id": 400,
        },
        "enabled": False,
    }
    return {
        "composite_key": f"{environment_api_key}_user_1_test",
        "identity_traits": [{"trait_value": "test", "trait_key": "first_name"}],
        "identity_features": [
            _environment_feature_state_1_document,
            _environment_feature_state_2_document,
            _mv_feature_state_document,
        ],
        "identifier": "user_1_test",
        "created_date": "2021-09-21T10:12:42.230257+00:00",
        "environment_api_key": environment_api_key,
        "identity_uuid": "59efa2a7-6a45-46d6-b953-a7073a90eacf",
    }


@pytest.fixture()
def identity_document_without_fs(identity_document):
    identity_document["identity_features"].clear()
    return identity_document

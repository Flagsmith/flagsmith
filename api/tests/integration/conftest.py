import json
import uuid

import pytest
from django.test import Client as DjangoClient
from django.urls import reverse
from rest_framework.test import APIClient

from app.utils import create_hash


@pytest.fixture()
def django_client():
    return DjangoClient()


@pytest.fixture()
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


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
def feature(admin_client, project):
    data = {
        "name": "test feature",
        "initial_value": "default_value",
        "project": project,
    }
    url = reverse("api-v1:projects:project-features-list", args=[project])

    response = admin_client.post(url, data=data)
    return response.json()["id"]


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
def identity_document(environment_api_key):
    _environment_feature_state_1_document = {
        "multivariate_feature_state_values": [],
        "feature_state_value": "feature_1_value",
        "id": 1,
        "feature": {
            "name": "feature_1",
            "type": "STANDARD",
            "id": 1,
        },
        "enabled": False,
    }
    _environment_feature_state_2_document = {
        "multivariate_feature_state_values": [],
        "feature_state_value": "2.3",
        "id": 2,
        "feature": {
            "name": "feature_2",
            "type": "STANDARD",
            "id": 2,
        },
        "enabled": True,
    }
    _mv_feature_state_document = {
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
        "id": 4,
        "feature": {
            "name": "multivariate_feature",
            "type": "MULTIVARIATE",
            "id": 4,
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


@pytest.fixture
def slack_bot_token():
    return "bot_token_test"


@pytest.fixture
def slack_project_config(
    mocker, django_client, environment, environment_api_key, slack_bot_token
):
    url = reverse(
        "api-v1:environments:integrations-slack-slack-oauth-callback",
        args=[environment_api_key],
    )
    mocker.patch("integrations.slack.views.get_bot_token", return_value=slack_bot_token)
    mocker.patch("integrations.slack.views.validate_state", return_value=True)
    django_client.get(f"{url}?state=state&code=code")


@pytest.fixture
def slack_environment_config(
    mocker, admin_client, environment, environment_api_key, slack_project_config
):
    url = reverse(
        "api-v1:environments:integrations-slack-list",
        args=[environment_api_key],
    )
    env_config = {"channel_id": "channel_id1", "enabled": True}
    mocker.patch("integrations.slack.models.join_channel")
    response = admin_client.post(
        url,
        data=json.dumps(env_config),
        content_type="application/json",
    )
    return response.json()["id"]

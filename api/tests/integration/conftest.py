import json
import uuid

import pytest
from django.test import Client as DjangoClient
from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from rest_framework import status
from rest_framework.test import APIClient

from app.utils import create_hash
from organisations.models import Organisation
from tests.integration.helpers import create_mv_option_with_api


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
def organisation_with_persist_trait_data_disabled(organisation):
    Organisation.objects.filter(id=organisation).update(persist_trait_data=False)


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
def environment_name() -> str:
    return "Test Environment"


@pytest.fixture()
def environment(
    admin_client: APIClient,
    project: int,
    environment_api_key: str,
    environment_name: str,
    settings: SettingsWrapper,
) -> int:
    settings.EDGE_RELEASE_DATETIME = None
    environment_data = {
        "name": environment_name,
        "api_key": environment_api_key,
        "project": project,
        "allow_client_traits": True,
    }
    url = reverse("api-v1:environments:environment-list")

    response = admin_client.post(url, data=environment_data)
    return response.json()["id"]


@pytest.fixture()
def dynamo_enabled_environment(
    admin_client: APIClient,
    dynamo_enabled_project: int,
    environment_api_key: str,
    app_settings_for_dynamodb: None,
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
    return str(uuid.uuid4())


@pytest.fixture()
def identity(admin_client, identity_identifier, environment, environment_api_key):
    identity_data = {"identifier": identity_identifier}
    url = reverse(
        "api-v1:environments:environment-identities-list", args=[environment_api_key]
    )
    response = admin_client.post(url, data=identity_data)
    return response.json()["id"]


@pytest.fixture()
def identity_with_traits_matching_segment(
    admin_client: APIClient,
    environment_api_key,
    identity: int,
    segment_condition_value: str,
    segment_condition_property: str,
) -> int:
    trait_data = {
        "trait_key": segment_condition_property,
        "string_value": segment_condition_value,
    }
    url = reverse(
        "api-v1:environments:identities-traits-list",
        args=[environment_api_key, identity],
    )
    res = admin_client.post(
        url, data=json.dumps(trait_data), content_type="application/json"
    )
    assert res.status_code == status.HTTP_201_CREATED
    return identity


@pytest.fixture()
def sdk_client(environment_api_key):
    client = APIClient()
    client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_api_key)
    return client


@pytest.fixture()
def server_side_sdk_client(
    admin_client: APIClient, environment: int, environment_api_key: str
) -> APIClient:
    url = reverse("api-v1:environments:api-keys-list", args={environment_api_key})
    response = admin_client.post(url, data={"name": "Some key"})

    client = APIClient()
    client.credentials(HTTP_X_ENVIRONMENT_KEY=response.json()["key"])
    return client


@pytest.fixture()
def default_feature_value():
    return "default_value"


@pytest.fixture()
def feature_name():
    return "feature_1"


@pytest.fixture()
def feature_2_name():
    return "feature_2"


@pytest.fixture()
def mv_feature_name():
    return "mv_feature"


@pytest.fixture()
def feature(admin_client, project, default_feature_value, feature_name):
    data = {
        "name": feature_name,
        "initial_value": default_feature_value,
        "project": project,
    }
    url = reverse("api-v1:projects:project-features-list", args=[project])

    response = admin_client.post(url, data=data)
    return response.json()["id"]


@pytest.fixture()
def mv_feature(admin_client, project, default_feature_value, mv_feature_name):
    data = {
        "name": mv_feature_name,
        "initial_value": default_feature_value,
        "project": project,
        "type": "MULTIVARIATE",
    }
    url = reverse("api-v1:projects:project-features-list", args=[project])

    response = admin_client.post(url, data=data)
    return response.json()["id"]


@pytest.fixture()
def mv_feature_option_value():
    return "foo"


@pytest.fixture()
def mv_feature_option(
    project: int,
    admin_client: "APIClient",
    mv_feature: int,
    mv_feature_option_value: str,
) -> int:
    data = {
        "string_value": mv_feature_option_value,
        "type": "unicode",
        "default_percentage_allocation": 0,
        "feature": mv_feature,
    }
    url = reverse("api-v1:projects:feature-mv-options-list", args=[project, mv_feature])
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    return response.json()["id"]


@pytest.fixture()
def feature_2(admin_client, project, default_feature_value, feature_2_name):
    data = {
        "name": feature_2_name,
        "initial_value": default_feature_value,
        "project": project,
    }
    url = reverse("api-v1:projects:project-features-list", args=[project])

    response = admin_client.post(url, data=data)
    return response.json()["id"]


@pytest.fixture()
def mv_option_50_percent(project, admin_client, feature, mv_option_value):
    return create_mv_option_with_api(
        admin_client, project, feature, 50, mv_option_value
    )


@pytest.fixture()
def segment_name():
    return "Test Segment"


@pytest.fixture()
def segment_condition_property():
    return "foo"


@pytest.fixture()
def segment_condition_value():
    return "bar"


@pytest.fixture()
def segment(
    admin_client,
    project,
    segment_name,
    segment_condition_property,
    segment_condition_value,
):
    url = reverse("api-v1:projects:project-segments-list", args=[project])
    data = {
        "name": segment_name,
        "project": project,
        "rules": [
            {
                "type": "ALL",
                "rules": [
                    {
                        "type": "ANY",
                        "rules": [],
                        "conditions": [
                            {
                                "property": segment_condition_property,
                                "operator": "EQUAL",
                                "value": segment_condition_value,
                            }
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
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
def segment_featurestate(
    admin_client: APIClient,
    segment: int,
    feature: int,
    environment: int,
    feature_segment: int,
) -> int:
    data = {
        "feature": feature,
        "environment": environment,
        "feature_segment": feature_segment,
    }
    url = reverse("api-v1:features:featurestates-list")
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    return response.json()["id"]


@pytest.fixture()
def identity_traits():
    return [
        {"trait_value": "trait_value_1", "trait_key": "trait_key_1"},
        {"trait_value": "trait_value_2", "trait_key": "trait_key_2"},
        {"trait_value": "trait_value_3", "trait_key": "trait_key_3"},
    ]


@pytest.fixture()
def identity_document(
    environment_api_key,
    feature_name,
    feature,
    identity_traits,
    feature_2_name,
    feature_2,
    mv_feature_name,
    mv_feature,
):
    _environment_feature_state_1_document = {
        "featurestate_uuid": "ad71c644-71df-4e83-9cb5-cd2cd0160200",
        "multivariate_feature_state_values": [],
        "feature_state_value": "feature_1_value",
        "django_id": 1,
        "feature": {
            "name": feature_name,
            "type": "STANDARD",
            "id": feature,
        },
        "enabled": False,
        "feature_segment": None,
    }
    _environment_feature_state_2_document = {
        "featurestate_uuid": "c6ec4de7-11a7-47c2-abc9-0d7bf0fc90e9",
        "multivariate_feature_state_values": [],
        "django_id": 1,
        "feature_state_value": "2.3",
        "feature": {
            "name": feature_2_name,
            "type": "STANDARD",
            "id": feature_2,
        },
        "enabled": True,
        "feature_segment": None,
    }
    _mv_feature_state_document = {
        "featurestate_uuid": "4a8fbe06-d4cd-4686-a184-d924844bb421",
        "multivariate_feature_state_values": [
            {
                "percentage_allocation": 50,
                "multivariate_feature_option": {"value": "50_percent", "id": 1},
                "mv_fs_value_uuid": "9438d56d-e06e-4f6b-bca5-f66755f063c0",
                "id": 1,
            },
            {
                "percentage_allocation": 50,
                "mv_fs_value_uuid": "2a9293f6-7c53-43bc-a7a3-689679239106",
                "multivariate_feature_option": {
                    "value": "other_50_percent",
                    "id": None,
                },
                "id": 2,
            },
        ],
        "feature_state_value": None,
        "django_id": 1,
        "feature": {
            "name": mv_feature_name,
            "type": "MULTIVARIATE",
            "id": mv_feature,
        },
        "enabled": False,
        "feature_segment": None,
    }
    return {
        "composite_key": f"{environment_api_key}_user_1_test",
        "identity_traits": identity_traits,
        "identity_features": [
            _environment_feature_state_1_document,
            _environment_feature_state_2_document,
            _mv_feature_state_document,
        ],
        "identifier": "user_1_test",
        "created_date": "2021-09-21T10:12:42.230257+00:00",
        "environment_api_key": environment_api_key,
        "identity_uuid": "59efa2a7-6a45-46d6-b953-a7073a90eacf",
        "django_id": None,
    }


@pytest.fixture()
def identity_document_without_fs(environment_api_key, identity_traits):
    return {
        "composite_key": f"{environment_api_key}_user_1_test",
        "identity_traits": identity_traits,
        "identity_features": [],
        "identifier": "user_1_test",
        "created_date": "2021-09-21T10:12:42.230257+00:00",
        "environment_api_key": environment_api_key,
        "identity_uuid": "59efa2a7-6a45-46d6-b953-a7073a90eacf",
        "django_id": None,
    }


@pytest.fixture()
def admin_master_api_key(organisation: int, admin_client: APIClient) -> dict:
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-list",
        args=[organisation],
    )
    data = {"name": "test_key", "organisation": organisation}
    response = admin_client.post(url, data=data)

    return response.json()


@pytest.fixture()
def admin_master_api_key_prefix(admin_master_api_key: dict) -> str:
    return admin_master_api_key["prefix"]


@pytest.fixture()
def admin_master_api_key_client(admin_master_api_key: dict) -> APIClient:
    # Can not use `api_client` fixture here because:
    # https://docs.pytest.org/en/6.2.x/fixture.html#fixtures-can-be-requested-more-than-once-per-test-return-values-are-cached
    api_client = APIClient()
    api_client.credentials(HTTP_AUTHORIZATION="Api-Key " + admin_master_api_key["key"])
    return api_client


@pytest.fixture()
def non_admin_client(organisation, django_user_model, api_client):
    user = django_user_model.objects.create(username="non_admin_user")
    user.add_organisation(Organisation.objects.get(id=organisation))
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture()
def feature_state(admin_client, environment, feature):
    base_url = reverse("api-v1:features:featurestates-list")
    url = f"{base_url}?environment={environment}?feature={feature}"

    response = admin_client.get(url)
    return response.json()["results"][0]["id"]


@pytest.fixture()
def identity_featurestate(admin_client, environment, feature, identity):
    url = reverse("api-v1:features:featurestates-list")
    data = {
        "enabled": True,
        "feature_state_value": {"type": "unicode", "string_value": "identity override"},
        "identity": identity,
        "environment": environment,
        "feature": feature,
    }
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    return response.json()["id"]

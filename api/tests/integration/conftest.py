import uuid

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from app.utils import create_hash


@pytest.fixture()
def admin_user(django_user_model):
    return django_user_model.objects.create(email="test@example.com")


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

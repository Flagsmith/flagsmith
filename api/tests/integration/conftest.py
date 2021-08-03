import pytest
from django.test import Client as DjangoClient
from rest_framework.test import APIClient


@pytest.fixture()
def django_client():
    return DjangoClient()


@pytest.fixture()
def sdk_client(environment_api_key):
    client = APIClient()
    client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_api_key)
    return client

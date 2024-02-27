from datetime import timedelta
from typing import Any

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.fixture()
def _expired_api_key(admin_client: APIClient, organisation: int) -> dict[str, Any]:
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-list",
        args=[organisation],
    )
    data = {
        "name": "test_key",
        "organisation": organisation,
        "expiry_date": timezone.now() - timedelta(hours=1),
    }
    response = admin_client.post(url, data=data)
    return response.json()


@pytest.fixture()
def expired_api_key_prefix(_expired_api_key: dict[str, Any]) -> str:
    return _expired_api_key["prefix"]

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture()
def trust_relationship(
    admin_client: APIClient,
    organisation: int,
) -> int:
    response = admin_client.post(
        f"/api/v1/organisations/{organisation}/trust-relationships/",
        data={
            "name": "GitHub Actions",
            "issuer": "https://token.actions.githubusercontent.com",
            "audience": "https://github.com/Flagsmith",
            "claim_rules": [{"claim": "repository", "values": ["Flagsmith/flagsmith"]}],
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["id"]  # type: ignore[no-any-return]

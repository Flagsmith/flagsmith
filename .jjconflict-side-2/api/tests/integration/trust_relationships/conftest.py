from typing import Generator

import jwt
import pytest
import responses as responses_lib
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from tests.test_helpers import OIDCIssuerStub
from trust_relationships.oidc import get_jwks_client


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
            "is_admin": True,
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["id"]  # type: ignore[no-any-return]


@pytest.fixture(autouse=True)
def clear_jwks_client_cache() -> Generator[None, None, None]:
    get_jwks_client.cache_clear()
    yield
    get_jwks_client.cache_clear()


@pytest.fixture()
def oidc_issuer(
    responses: responses_lib.RequestsMock,
    mocker: MockerFixture,
) -> OIDCIssuerStub:
    issuer = OIDCIssuerStub("https://token.actions.githubusercontent.com")
    # Rejections short-circuiting before discovery are expected.
    responses.assert_all_requests_are_fired = False
    responses.add(
        responses_lib.GET,
        "https://token.actions.githubusercontent.com/.well-known/openid-configuration",
        json={
            "jwks_uri": "https://token.actions.githubusercontent.com/.well-known/jwks"
        },
    )
    mocker.patch.object(jwt.PyJWKClient, "fetch_data", return_value=issuer.jwks)
    return issuer


@pytest.fixture()
def machine_client() -> APIClient:
    # A client that is never force-authenticated
    return APIClient()

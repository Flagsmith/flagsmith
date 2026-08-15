from typing import Generator

import jwt
import pytest
import responses as responses_lib
from pytest_mock import MockerFixture

from organisations.models import Organisation
from tests.test_helpers import OIDCIssuerStub
from trust_relationships.models import TrustRelationship
from trust_relationships.oidc import get_jwks_client
from trust_relationships.services import create_trust_relationship


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
def github_trust_relationship(organisation: Organisation) -> TrustRelationship:
    return create_trust_relationship(
        organisation_id=organisation.id,
        name="GitHub Actions",
        issuer="https://token.actions.githubusercontent.com",
        audience="https://github.com/Flagsmith",
        is_admin=True,
        claim_rules=[{"claim": "repository", "values": ["Flagsmith/*"]}],
    )

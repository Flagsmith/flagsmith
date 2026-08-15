import pytest
from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from trust_relationships.authentication import (
    TrustRelationshipTokenAuthentication,
)
from trust_relationships.models import TrustRelationship
from trust_relationships.services import mint_access_token


def test_authenticate__no_bearer_header__returns_none() -> None:
    # Given
    request = Request(
        APIRequestFactory().get("/", HTTP_AUTHORIZATION="Api-Key some-key")
    )

    # When
    result = TrustRelationshipTokenAuthentication().authenticate(request)

    # Then
    assert result is None


def test_authenticate__foreign_bearer_token__returns_none() -> None:
    # Given
    request = Request(
        APIRequestFactory().get("/", HTTP_AUTHORIZATION="Bearer not-one-of-ours")
    )

    # When
    result = TrustRelationshipTokenAuthentication().authenticate(request)

    # Then
    assert result is None


def test_authenticate__revoked_backing_key__raises_authentication_failed(
    github_trust_relationship: TrustRelationship,
) -> None:
    # Given
    result = mint_access_token(
        github_trust_relationship,
        sub="repo:Flagsmith/flagsmith:ref:refs/heads/main",
    )
    backing_key = github_trust_relationship.master_api_key
    backing_key.revoked = True
    backing_key.save()
    request = Request(
        APIRequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {result.access_token}")
    )

    # When / Then
    with pytest.raises(exceptions.AuthenticationFailed):
        TrustRelationshipTokenAuthentication().authenticate(request)

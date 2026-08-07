from rest_framework import status
from rest_framework.test import APIClient

from tests.test_helpers import OIDCIssuerStub


def test_token_exchange__matching_token__returns_usable_access_token(
    machine_client: APIClient,
    organisation: int,
    trust_relationship: int,
    oidc_issuer: OIDCIssuerStub,
) -> None:
    # Given
    token = oidc_issuer.sign_token(
        aud="https://github.com/Flagsmith",
        sub="repo:Flagsmith/flagsmith:ref:refs/heads/main",
        repository="Flagsmith/flagsmith",
    )

    # When
    response = machine_client.post(
        "/api/v1/auth/oidc/token/", data={"token": token}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["token_type"] == "Bearer"
    assert response_json["expires_in"] == 3600

    # And the minted token authenticates against the admin API
    machine_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {response_json['access_token']}"
    )
    organisations_response = machine_client.get("/api/v1/organisations/")
    assert organisations_response.status_code == status.HTTP_200_OK
    assert organisations_response.json()["results"][0]["id"] == organisation


def test_token_exchange__deleted_trust_relationship__access_token_rejected(
    machine_client: APIClient,
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
    oidc_issuer: OIDCIssuerStub,
) -> None:
    # Given
    token = oidc_issuer.sign_token(
        aud="https://github.com/Flagsmith",
        sub="repo:Flagsmith/flagsmith:ref:refs/heads/main",
        repository="Flagsmith/flagsmith",
    )
    access_token = machine_client.post(
        "/api/v1/auth/oidc/token/", data={"token": token}, format="json"
    ).json()["access_token"]
    admin_client.delete(
        f"/api/v1/organisations/{organisation}"
        f"/trust-relationships/{trust_relationship}/"
    )

    # When
    machine_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    response = machine_client.get("/api/v1/organisations/")

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_token_exchange__minted_token__cannot_manage_machine_credentials(
    machine_client: APIClient,
    organisation: int,
    trust_relationship: int,
    oidc_issuer: OIDCIssuerStub,
) -> None:
    # Given
    token = oidc_issuer.sign_token(
        aud="https://github.com/Flagsmith",
        sub="repo:Flagsmith/flagsmith:ref:refs/heads/main",
        repository="Flagsmith/flagsmith",
    )
    access_token = machine_client.post(
        "/api/v1/auth/oidc/token/", data={"token": token}, format="json"
    ).json()["access_token"]
    machine_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # When
    master_api_keys_response = machine_client.post(
        f"/api/v1/organisations/{organisation}/master-api-keys/",
        data={"name": "sneaky", "organisation": organisation},
    )
    trust_relationships_response = machine_client.get(
        f"/api/v1/organisations/{organisation}/trust-relationships/"
    )

    # Then
    assert master_api_keys_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert trust_relationships_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_token_exchange__no_matching_trust_relationship__returns_401(
    machine_client: APIClient,
    trust_relationship: int,
    oidc_issuer: OIDCIssuerStub,
) -> None:
    # Given
    token = oidc_issuer.sign_token(
        aud="https://github.com/Flagsmith",
        sub="repo:SomeoneElse/repo:ref:refs/heads/main",
        repository="SomeoneElse/repo",
    )

    # When
    response = machine_client.post(
        "/api/v1/auth/oidc/token/", data={"token": token}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_token_exchange__multi_audience_token_matching_multiple__returns_401(
    machine_client: APIClient,
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
    oidc_issuer: OIDCIssuerStub,
) -> None:
    # Given: a second trust relationship under a different audience, and a
    # token listing both audiences
    admin_client.post(
        f"/api/v1/organisations/{organisation}/trust-relationships/",
        data={
            "name": "GitHub Actions (CI)",
            "issuer": "https://token.actions.githubusercontent.com",
            "audience": "flagsmith-ci",
        },
        format="json",
    )
    token = oidc_issuer.sign_token(
        aud=["https://github.com/Flagsmith", "flagsmith-ci"],
        sub="repo:Flagsmith/flagsmith:ref:refs/heads/main",
        repository="Flagsmith/flagsmith",
    )

    # When
    response = machine_client.post(
        "/api/v1/auth/oidc/token/", data={"token": token}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == (
        "Token audience matches multiple trust relationships."
    )


def test_token_exchange__missing_token__returns_400(
    machine_client: APIClient,
) -> None:
    # Given / When
    response = machine_client.post("/api/v1/auth/oidc/token/", data={}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

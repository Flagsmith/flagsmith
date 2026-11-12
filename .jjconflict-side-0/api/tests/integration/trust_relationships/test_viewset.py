from pytest_django.fixtures import SettingsWrapper
from rest_framework import status
from rest_framework.test import APIClient


def test_create_trust_relationship__valid_data__returns_backing_key_details(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "GitHub Actions",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "https://github.com/Flagsmith",
        "claim_rules": [{"claim": "repository", "values": ["Flagsmith/flagsmith"]}],
        "is_admin": True,
    }

    # When
    response = admin_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["name"] == "GitHub Actions"
    assert response_json["issuer"] == "https://token.actions.githubusercontent.com"
    assert response_json["is_admin"] is True
    assert response_json["master_api_key_prefix"]
    assert response_json["master_api_key_id"]
    assert response_json["claim_rules"] == [
        {"claim": "repository", "values": ["Flagsmith/flagsmith"]}
    ]


def test_create_trust_relationship__trailing_slash_issuer__returns_issuer_verbatim(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given: an issuer that ends in a slash, as Auth0's does. `iss` is matched
    # by exact string at exchange time, so the slash must survive the round trip.
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "Auth0",
        "issuer": "https://tenant.eu.auth0.com/",
        "audience": "https://api.flagsmith.com",
        "is_admin": True,
    }

    # When
    response = admin_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["issuer"] == "https://tenant.eu.auth0.com/"


def test_create_trust_relationship__http_issuer__returns_400(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "GitHub Actions",
        "issuer": "http://token.actions.githubusercontent.com",
        "audience": "https://github.com/Flagsmith",
        "is_admin": True,
    }

    # When
    response = admin_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["issuer"] == ["Issuer must be an https:// URL."]


def test_create_trust_relationship__non_admin_without_rbac__returns_400(
    admin_client: APIClient,
    organisation: int,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.IS_RBAC_INSTALLED = False
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "GitHub Actions",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "https://github.com/Flagsmith",
        "is_admin": False,
    }

    # When
    response = admin_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["is_admin"] == [
        "RBAC is not installed, cannot create non-admin trust relationship"
    ]


def test_create_trust_relationship__malformed_claim_rules__returns_400(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "GitHub Actions",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "https://github.com/Flagsmith",
        "claim_rules": [{"claim": "repository", "values": []}],
        "is_admin": True,
    }

    # When
    response = admin_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["claim_rules"] == [
        {"values": ["Ensure this field has at least 1 elements."]}
    ]


def test_list_trust_relationships__existing__returns_trust_relationships(
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["id"] == trust_relationship


def test_update_trust_relationship__new_values__returns_updated_values(
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
) -> None:
    # Given
    url = (
        f"/api/v1/organisations/{organisation}"
        f"/trust-relationships/{trust_relationship}/"
    )
    data = {
        "name": "GitHub Actions (prod)",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "flagsmith-prod",
        "claim_rules": [{"claim": "environment", "values": ["production"]}],
        "is_admin": True,
    }

    # When
    response = admin_client.put(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "GitHub Actions (prod)"
    assert response.json()["audience"] == "flagsmith-prod"
    assert response.json()["claim_rules"] == [
        {"claim": "environment", "values": ["production"]}
    ]


def test_create_trust_relationship__missing_is_admin__returns_400(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "GitHub Actions",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "https://github.com/Flagsmith",
    }

    # When
    response = admin_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["is_admin"] == ["This field is required."]


def test_update_trust_relationship__missing_is_admin__returns_400(
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
) -> None:
    # Given: a full update that forgets is_admin must not silently escalate
    # the trust relationship's privileges
    url = (
        f"/api/v1/organisations/{organisation}"
        f"/trust-relationships/{trust_relationship}/"
    )
    data = {
        "name": "GitHub Actions (prod)",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "flagsmith-prod",
    }

    # When
    response = admin_client.put(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["is_admin"] == ["This field is required."]


def test_partial_update_trust_relationship__omitted_is_admin__preserves_is_admin(
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.IS_RBAC_INSTALLED = True
    url = (
        f"/api/v1/organisations/{organisation}"
        f"/trust-relationships/{trust_relationship}/"
    )
    assert (
        admin_client.patch(url, data={"is_admin": False}, format="json").json()[
            "is_admin"
        ]
        is False
    )

    # When
    response = admin_client.patch(
        url, data={"name": "GitHub Actions (prod)"}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "GitHub Actions (prod)"
    assert response.json()["is_admin"] is False


def test_delete_trust_relationship__existing__removes_trust_relationship(
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
) -> None:
    # Given
    detail_url = (
        f"/api/v1/organisations/{organisation}"
        f"/trust-relationships/{trust_relationship}/"
    )
    list_url = f"/api/v1/organisations/{organisation}/trust-relationships/"

    # When
    response = admin_client.delete(detail_url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert admin_client.get(list_url).json()["count"] == 0


def test_list_master_api_keys__trust_relationship_exists__hides_backing_key(
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation}/master-api-keys/"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0


def test_create_trust_relationship__master_api_key_auth__returns_401(
    organisation: int,
    admin_master_api_key_client: APIClient,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "GitHub Actions",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "https://github.com/Flagsmith",
        "is_admin": True,
    }

    # When
    response = admin_master_api_key_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_trust_relationship__duplicate_issuer_and_audience__returns_400(
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "GitHub Actions (duplicate)",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "https://github.com/Flagsmith",
        "is_admin": True,
    }

    # When
    response = admin_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == [
        "The fields issuer, audience must make a unique set."
    ]


def test_update_trust_relationship__duplicate_issuer_and_audience__returns_400(
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
) -> None:
    # Given
    create_response = admin_client.post(
        f"/api/v1/organisations/{organisation}/trust-relationships/",
        data={
            "name": "GitLab CI",
            "issuer": "https://gitlab.com",
            "audience": "https://gitlab.com/Flagsmith",
            "is_admin": True,
        },
        format="json",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    url = (
        f"/api/v1/organisations/{organisation}"
        f"/trust-relationships/{create_response.json()['id']}/"
    )
    data = {
        "name": "GitLab CI",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "https://github.com/Flagsmith",
        "is_admin": True,
    }

    # When
    response = admin_client.put(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == [
        "The fields issuer, audience must make a unique set."
    ]


def test_create_trust_relationship__same_issuer_and_audience_as_deleted__returns_201(
    admin_client: APIClient,
    organisation: int,
    trust_relationship: int,
) -> None:
    # Given
    delete_response = admin_client.delete(
        f"/api/v1/organisations/{organisation}"
        f"/trust-relationships/{trust_relationship}/"
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "GitHub Actions (recreated)",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "https://github.com/Flagsmith",
        "is_admin": True,
    }

    # When
    response = admin_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_create_trust_relationship__long_name__returns_201(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given: a name long enough that the derived backing key name would
    # exceed MasterAPIKey.name's 50-character limit
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "GitHub Actions (Flagsmith/flagsmith-workflow-tools)",
        "issuer": "https://token.actions.githubusercontent.com",
        "audience": "https://github.com/Flagsmith/flagsmith-workflow-tools",
        "is_admin": True,
    }

    # When
    response = admin_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_create_trust_relationship__issuer_with_query_string__returns_400(
    admin_client: APIClient,
    organisation: int,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation}/trust-relationships/"
    data = {
        "name": "GitHub Actions",
        "issuer": "https://token.actions.githubusercontent.com?ref=main",
        "audience": "https://github.com/Flagsmith",
        "is_admin": True,
    }

    # When
    response = admin_client.post(url, data=data, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["issuer"] == [
        "Issuer must not contain a query string or fragment."
    ]

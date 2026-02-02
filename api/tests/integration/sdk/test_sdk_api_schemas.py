import json

from flagsmith_schemas import api as schemas
from pydantic import TypeAdapter
from rest_framework import status
from rest_framework.test import APIClient


def test_get_identities__valid_request__returns_response_conforming_to_schema(
    sdk_client: APIClient,
    feature: int,
    mv_feature: int,
    mv_feature_option: int,
    environment: int,
) -> None:
    # Given
    identifier = "test-user-123"
    url = "/api/v1/identities/"

    # When
    response = sdk_client.get(f"{url}?identifier={identifier}")

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    # Should not raise validation error
    TypeAdapter(schemas.V1IdentitiesResponse).validate_python(
        response_data,
        extra="ignore",  # TODO remove `extra="ignore"` https://github.com/Flagsmith/flagsmith/issues/6625
    )


def test_post_identities__with_traits__returns_response_conforming_to_schema(
    sdk_client: APIClient,
    feature: int,
    mv_feature: int,
    mv_feature_option: int,
    environment: int,
) -> None:
    # Given
    request_data = {
        "identifier": "user-with-traits",
        "traits": [
            {"trait_key": "email", "trait_value": "test@example.com"},
            {"trait_key": "age", "trait_value": 30},
            {"trait_key": "is_premium", "trait_value": True},
        ],
    }

    # Validate request conforms to schema
    request_adapter = TypeAdapter(schemas.V1IdentitiesRequest)
    request_adapter.validate_python(request_data, extra="ignore")

    url = "/api/v1/identities/"

    # When
    response = sdk_client.post(
        url,
        data=json.dumps(request_data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    # Should not raise validation error
    TypeAdapter(schemas.V1IdentitiesResponse).validate_python(
        response_data,
        extra="ignore",  # TODO remove `extra="ignore"` https://github.com/Flagsmith/flagsmith/issues/6625
    )


def test_get_identities__with_feature_filter__returns_single_flag_conforming_to_schema(
    sdk_client: APIClient,
    feature: int,
    feature_name: str,
    environment: int,
) -> None:
    # Given
    identifier = "test-user"
    url = "/api/v1/identities/"

    # When
    response = sdk_client.get(f"{url}?identifier={identifier}&feature={feature_name}")

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    # Should not raise validation error
    TypeAdapter(schemas.V1Flag).validate_python(
        response_data,
        extra="ignore",  # TODO remove `extra="ignore"` https://github.com/Flagsmith/flagsmith/issues/6625
    )


def test_get_environment_document__valid_request__returns_response_conforming_to_schema(
    server_side_sdk_client: APIClient,
    feature: int,
    mv_feature: int,
    mv_feature_option: int,
    environment: int,
) -> None:
    # Given
    url = "/api/v1/environment-document/"

    # When
    response = server_side_sdk_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    # Should not raise validation error
    TypeAdapter(schemas.V1EnvironmentDocumentResponse).validate_python(
        response_data,
        extra="ignore",  # TODO remove `extra="ignore"` https://github.com/Flagsmith/flagsmith/issues/6625
    )


def test_get_flags__valid_request__returns_list_conforming_to_schema(
    sdk_client: APIClient,
    feature: int,
    mv_feature: int,
    mv_feature_option: int,
    environment: int,
) -> None:
    # Given
    url = "/api/v1/flags/"

    # When
    response = sdk_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_data = response.json()
    TypeAdapter(schemas.V1FlagsResponse).validate_python(
        response_data,
        extra="ignore",  # TODO remove `extra="ignore"` https://github.com/Flagsmith/flagsmith/issues/6625
    )

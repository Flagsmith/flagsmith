import pytest
from rest_framework.test import APIClient

from features.future.types import UpdateFlagRequest
from features.models import Feature
from tests.integration.helpers import create_mv_option_with_api

pytestmark = pytest.mark.usefixtures("versioned_environment")


@pytest.fixture()
def egg(admin_client: APIClient, environment_api_key: str, project: int) -> int:
    egg = Feature.objects.create(name="egg", project_id=project, initial_value="wild")
    chicken = Feature.objects.create(name="chicken", project_id=project)
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{egg.id}/dependencies/{chicken.id}/",
    )
    assert response.status_code == 201
    return egg.id  # type: ignore[no-any-return]


def test_get_flags__dependent_flag_default_value_changed__serves_current_value(
    admin_client: APIClient,
    egg: int,
    environment_api_key: str,
    sdk_client: APIClient,
) -> None:
    # Given
    admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{egg}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "enabled": True,
                    "value": {"type": "string", "value": "farm"},
                }
            }
        ),
        format="json",
    )

    # When
    response = sdk_client.get("/api/v1/flags/")

    # Then
    assert response.status_code == 200
    assert {
        flag["feature"]["name"]: (flag["enabled"], flag["feature_state_value"])
        for flag in response.json()
    } == {"egg": (False, "farm"), "chicken": (False, None)}


def test_get_identity_flags__dependent_flag_default_variants_changed__serves_current_variant(
    admin_client: APIClient,
    environment_api_key: str,
    project: int,
    sdk_client: APIClient,
) -> None:
    # Given
    egg = Feature.objects.create(
        name="egg", project_id=project, type="MULTIVARIATE", initial_value="wild"
    )
    chicken = Feature.objects.create(name="chicken", project_id=project)
    farm = create_mv_option_with_api(admin_client, project, egg.id, 0, "farm")
    admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{egg.id}/dependencies/{chicken.id}/",
    )
    admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{egg.id}/",
        UpdateFlagRequest(
            {"environment_default": {"variants": [{"id": farm, "weight": 100}]}}
        ),
        format="json",
    )

    # When
    response = sdk_client.get("/api/v1/identities/", {"identifier": "hen"})

    # Then
    assert response.status_code == 200
    assert {
        flag["feature"]["name"]: (flag["enabled"], flag["feature_state_value"])
        for flag in response.json()["flags"]
    } == {"egg": (False, "farm"), "chicken": (False, None)}


def test_get_environment_document__dependent_flag_default_value_changed__serves_current_value(
    admin_client: APIClient,
    egg: int,
    environment_api_key: str,
    server_side_sdk_client: APIClient,
) -> None:
    # Given
    admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{egg}/",
        UpdateFlagRequest(
            {
                "environment_default": {
                    "enabled": True,
                    "value": {"type": "string", "value": "farm"},
                }
            }
        ),
        format="json",
    )

    # When
    response = server_side_sdk_client.get("/api/v1/environment-document/")

    # Then
    assert response.status_code == 200
    [segment] = response.json()["project"]["segments"]
    assert [
        (feature_state["enabled"], feature_state["feature_state_value"])
        for feature_state in segment["feature_states"]
    ] == [(False, "farm")]

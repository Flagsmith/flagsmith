from rest_framework.test import APIClient


def test_api_documentation_specification_loads(
    client: APIClient,
) -> None:
    # When
    response = client.get("/api/v1/docs/?format=openapi")

    # Then
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Flagsmith API"

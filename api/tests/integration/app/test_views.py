from rest_framework.test import APIClient


def test_liveness_probe__return_expected(client: APIClient) -> None:
    response = client.get("/health/liveness/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

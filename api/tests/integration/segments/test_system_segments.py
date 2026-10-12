from rest_framework.test import APIClient

from segments.models import Segment


def test_create_segment__version_of_system_segment__responds_409(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    feature: int,
    feature_2: int,
    project: int,
) -> None:
    # Given
    system_segment = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature}"
        f"/dependencies/{feature_2}/",
    ).json()["segment"]["id"]

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/segments/",
        {
            "name": "Not a dependency",
            "project": project,
            "version_of": system_segment,
            "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        },
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == {
        "code": "system_segment_modification",
        "message": (
            "System segments and their overrides can't be changed directly. "
            "Change this one through its flag dependency instead."
        ),
    }


def test_create_segment__version_of_segment__responds_201(
    admin_client: APIClient,
    project: int,
    segment: int,
) -> None:
    """Change requests to segments draft new versions of them."""
    # Given / When
    response = admin_client.post(
        f"/api/v1/projects/{project}/segments/",
        {
            "name": "New version",
            "project": project,
            "version_of": segment,
            "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        },
        format="json",
    )

    # Then
    assert response.status_code == 201
    assert response.json()["version_of"] == segment


def test_create_segment__version_of_unmanaged_system_segment__responds_409(
    admin_client: APIClient,
    project: int,
) -> None:
    # Given
    system_segment = Segment.objects.create(
        name="system", project_id=project, is_system_segment=True
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/segments/",
        {
            "name": "Not a system segment",
            "project": project,
            "version_of": system_segment.id,
            "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        },
        format="json",
    )

    # Then
    assert response.status_code == 409
    assert response.json() == {
        "code": "system_segment_modification",
        "message": "System segments and their overrides can't be changed directly.",
    }

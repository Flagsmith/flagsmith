from rest_framework.test import APIClient

from projects.models import Project


def test_get_logs__member_but_not_admin__responds_403(
    non_admin_client: APIClient,
    project: int,
) -> None:
    # Given / When
    response = non_admin_client.get(f"/api/v1/projects/{project}/audit/")

    # Then
    assert response.status_code == 403
    assert response.json() == {
        "detail": "You do not have permission to perform this action."
    }


def test_get_logs__project_not_found__responds_404(
    admin_client: APIClient,
) -> None:
    # Given
    Project.objects.filter(id=999999).delete()  # 🤷

    # When
    response = admin_client.get("/api/v1/projects/999999/audit/")

    # Then
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}

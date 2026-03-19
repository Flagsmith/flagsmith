from django.urls import reverse
from rest_framework import status


def test_get_all_user_permissions__admin_user__returns_admin_with_empty_permissions(
    project, admin_user, admin_client
):  # type: ignore[no-untyped-def]
    """Basic integration test to verify that endpoint works"""
    # Given
    url = reverse("api-v1:projects:all-user-permissions", args=(project, admin_user.id))

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["admin"] is True
    assert response_json["permissions"] == []

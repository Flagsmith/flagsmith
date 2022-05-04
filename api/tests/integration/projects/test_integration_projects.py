from django.urls import reverse
from rest_framework import status


def test_get_all_user_permissions(project, admin_user, admin_client):
    """Basic integration test to verify that endpoint works"""
    url = reverse("api-v1:projects:all-user-permissions", args=(project, admin_user.id))
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert response_json["admin"] is True
    assert response_json["permissions"] == []

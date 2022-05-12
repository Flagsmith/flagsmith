from django.urls import reverse


def test_response_have_cache_control_headers(project, admin_user, admin_client):
    # Given - any endpoint
    url = reverse("api-v1:projects:all-user-permissions", args=(project, admin_user.id))
    # When
    response = admin_client.get(url)
    # Then
    assert (
        response.headers["Cache-Control"]
        == "max-age=0, no-cache, no-store, must-revalidate, private"
    )
    assert response.headers["Pragma"] == "no-cache"

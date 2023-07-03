from django.urls import reverse
from rest_framework import status


def test_users_cannot_remove_members_from_another_organisation(
    organisation_one,
    organisation_two,
    organisation_one_admin_user,
    organisation_two_user,
    api_client,
):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-remove-users", args=[organisation_two.id]
    )
    api_client.force_authenticate(organisation_one_admin_user)

    # When
    response = api_client.post(url, data={"users": [organisation_two_user.id]})

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert organisation_two.users.filter(id=organisation_two_user.id).exists()

from django.urls import reverse
from rest_framework import status


def test_user_with_view_environment_permission_can_retrieve_all_feature_states_for_identity(
    test_user_client,
    environment,
    feature,
    view_environment_permission,
    user_environment_permission,
    identity_document_without_fs,
    edge_identity_dynamo_wrapper_mock,
):
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document_without_fs
    )
    user_environment_permission.permissions.add(view_environment_permission)
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-all",
        args=(environment.api_key, identity_document_without_fs["identity_uuid"]),
    )

    # When
    response = test_user_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1

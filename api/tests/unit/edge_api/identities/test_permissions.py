from edge_api.identities.permissions import (
    EdgeIdentityWithIdentifierViewPermissions,
)
from environments.permissions.constants import UPDATE_FEATURE_STATE


def test_edge_identity_with_identifier_view_permissions_has_permissions_calls_has_environment_permission(
    environment,
    mocker,
):
    # Given
    permissions = EdgeIdentityWithIdentifierViewPermissions()
    request = mocker.Mock()
    view = mocker.Mock(kwargs=dict(environment_api_key=environment.api_key))

    # When
    has_permission = permissions.has_permission(request, view)

    # Then
    request.user.has_environment_permission.assert_called_once_with(
        UPDATE_FEATURE_STATE, environment
    )
    assert has_permission == request.user.has_environment_permission.return_value

from common.environments.permissions import UPDATE_FEATURE_STATE  # type: ignore[import-untyped]

from edge_api.identities.permissions import (
    EdgeIdentityWithIdentifierViewPermissions,
)


def test_edge_identity_with_identifier_view_permissions_has_permissions_calls_has_environment_permission(  # type: ignore[no-untyped-def]  # noqa: E501
    environment,
    mocker,
):
    # Given
    permissions = EdgeIdentityWithIdentifierViewPermissions()
    request = mocker.Mock()
    view = mocker.Mock(kwargs=dict(environment_api_key=environment.api_key))

    # When
    has_permission = permissions.has_permission(request, view)  # type: ignore[no-untyped-call]

    # Then
    request.user.has_environment_permission.assert_called_once_with(
        UPDATE_FEATURE_STATE, environment
    )
    assert has_permission == request.user.has_environment_permission.return_value

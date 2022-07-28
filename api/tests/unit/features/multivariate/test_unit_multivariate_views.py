from features.multivariate.views import MultivariateFeatureOptionViewSet
from projects.permissions import NestedProjectPermissions


def test_multivariate_feature_options_view_set_get_permissions():
    # Given
    view_set = MultivariateFeatureOptionViewSet()

    # When
    permissions = view_set.get_permissions()

    # Then
    assert len(permissions) == 2
    assert isinstance(permissions[1], NestedProjectPermissions)
    assert permissions[1].action_permission_map == {
        "list": "VIEW_PROJECT",
        "detail": "VIEW_PROJECT",
        "create": "CREATE_FEATURE",
        "update": "CREATE_FEATURE",
        "partial_update": "CREATE_FEATURE",
        "destroy": "CREATE_FEATURE",
    }

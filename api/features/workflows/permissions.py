from rest_framework.permissions import BasePermission

from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)


class ChangeRequestPermissions(BasePermission):
    def has_permission(self, request, view):
        if view.action == "list":
            environment_id = request.query_params.get("environment")
            return environment_id and environment_id in [
                env.id
                for env in request.user.get_permitted_environments(VIEW_ENVIRONMENT)
            ]

        return True

    def has_object_permission(self, request, view, obj):
        return request.user.has_environment_permission(
            UPDATE_FEATURE_STATE, obj.environment
        )

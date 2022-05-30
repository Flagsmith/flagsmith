from rest_framework.permissions import BasePermission

from environments.models import Environment
from environments.permissions.constants import UPDATE_FEATURE_STATE
from projects.models import Project

ACTION_PERMISSIONS_MAP = {
    "retrieve": "VIEW_PROJECT",
    "destroy": "DELETE_FEATURE",
    "list": "VIEW_PROJECT",
    "create": "CREATE_FEATURE",
    "add_owners": "CREATE_FEATURE",
    "remove_owners": "CREATE_FEATURE",
    "update": "CREATE_FEATURE",
    "partial_update": "CREATE_FEATURE",
}


class FeaturePermissions(BasePermission):
    def has_permission(self, request, view):
        try:
            project_id = view.kwargs.get("project_pk") or request.data.get("project")
            project = Project.objects.get(id=project_id)

            if view.action in ACTION_PERMISSIONS_MAP:
                return request.user.has_project_permission(
                    ACTION_PERMISSIONS_MAP.get(view.action), project
                )

            # move on to object specific permissions
            return view.detail

        except Project.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        # map of actions and their required permission
        if view.action in ACTION_PERMISSIONS_MAP:
            return request.user.has_project_permission(
                ACTION_PERMISSIONS_MAP[view.action], obj.project
            )

        if view.action == "segments":
            return request.user.is_project_admin(obj.project)

        return False


class FeatureStatePermissions(BasePermission):
    def has_permission(self, request, view):
        try:
            if view.action == "create" and request.data.get("environment"):
                environment = Environment.objects.get(id=request.data["environment"])
                return request.user.has_environment_permission(
                    UPDATE_FEATURE_STATE, environment
                )

            # - detail view means we can just defer to object permissions
            # - list view means we just need to filter the objects based on permissions
            return view.detail or view.action == "list"

        except Environment.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        return request.user.has_environment_permission(
            UPDATE_FEATURE_STATE, environment=obj.environment
        )


class EnvironmentFeatureStatePermissions(BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            environment_api_key = view.kwargs.get("environment_api_key")
            if not environment_api_key:
                return False

            environment = Environment.objects.get(api_key=environment_api_key)
            return request.user.has_environment_permission(
                permission=UPDATE_FEATURE_STATE, environment=environment
            )

        if view.action == "list":
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        return request.user.has_environment_permission(
            permission=UPDATE_FEATURE_STATE, environment=obj.environment
        )


class IdentityFeatureStatePermissions(EnvironmentFeatureStatePermissions):
    pass

from contextlib import suppress

from django.http import HttpRequest
from rest_framework.permissions import BasePermission, IsAuthenticated

from environments.models import Environment
from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from features.models import FeatureState
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


class FeatureStatePermissions(IsAuthenticated):
    def has_permission(self, request, view):
        action_permission_map = {
            "list": VIEW_ENVIRONMENT,
            "create": UPDATE_FEATURE_STATE,
        }
        if not super().has_permission(request, view):
            return False

        # detail view means we can just defer to object permissions
        if view.detail:
            return True

        try:
            environment = request.data.get("environment") or request.query_params.get(
                "environment"
            )

            if environment and (isinstance(environment, int) or environment.isdigit()):
                environment = Environment.objects.get(id=int(environment))
                return request.user.has_environment_permission(
                    action_permission_map.get(view.action), environment
                )
            return False

        except Environment.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_anonymous:
            return False

        return request.user.has_environment_permission(
            UPDATE_FEATURE_STATE, environment=obj.environment
        )


class MasterAPIKeyFeatureStatePermissions(BasePermission):
    def has_permission(self, request: HttpRequest, view: str) -> bool:
        master_api_key = getattr(request, "master_api_key", None)
        if not master_api_key:
            return False
        environment = request.data.get("environment") or request.query_params.get(
            "environment"
        )
        if environment and (isinstance(environment, int) or environment.isdigit()):
            with suppress(Environment.DoesNotExist):
                environment = Environment.objects.get(id=int(environment))
                return environment.project.organisation == master_api_key.organisation
        return False

    def has_object_permission(
        self, request: HttpRequest, view: str, obj: FeatureState
    ) -> bool:
        master_api_key = getattr(request, "master_api_key", None)
        if master_api_key:
            return obj.environment.project.organisation == master_api_key.organisation
        return False


class MasterAPIKeyEnvironmentFeatureStatePermissions(BasePermission):
    def has_permission(self, request: HttpRequest, view: str) -> bool:
        master_api_key = getattr(request, "master_api_key", None)
        if not master_api_key:
            return False
        environment_api_key = view.kwargs.get("environment_api_key")
        if not environment_api_key:
            return False

        with suppress(Environment.DoesNotExist):
            environment = Environment.objects.get(api_key=environment_api_key)
            return environment.project.organisation == master_api_key.organisation
        return False

    def has_object_permission(
        self, request: HttpRequest, view: str, obj: FeatureState
    ) -> bool:
        master_api_key = getattr(request, "master_api_key", None)
        if master_api_key:
            return obj.environment.project.organisation == master_api_key.organisation
        return False


class EnvironmentFeatureStatePermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

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
        if request.user.is_anonymous:
            return False
        return request.user.has_environment_permission(
            permission=UPDATE_FEATURE_STATE, environment=obj.environment
        )


class IdentityFeatureStatePermissions(EnvironmentFeatureStatePermissions):
    pass

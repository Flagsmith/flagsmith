from contextlib import suppress

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated

from environments.models import Environment
from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from projects.models import Project
from projects.permissions import CREATE_FEATURE, DELETE_FEATURE, VIEW_PROJECT

ACTION_PERMISSIONS_MAP = {
    "retrieve": VIEW_PROJECT,
    "destroy": DELETE_FEATURE,
    "list": VIEW_PROJECT,
    "create": CREATE_FEATURE,
    "add_owners": CREATE_FEATURE,
    "remove_owners": CREATE_FEATURE,
    "update": CREATE_FEATURE,
    "partial_update": CREATE_FEATURE,
}


class FeaturePermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

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
        return request.user.has_environment_permission(
            UPDATE_FEATURE_STATE, environment=obj.environment
        )


class EnvironmentFeatureStatePermissions(IsAuthenticated):
    def has_permission(self, request, view):
        action_permission_map = {
            "list": VIEW_ENVIRONMENT,
            "create": UPDATE_FEATURE_STATE,
            "all": VIEW_ENVIRONMENT,
        }
        if not super().has_permission(request, view):
            return False

        # detail view means we can just defer to object permissions
        if view.detail:
            return True

        environment_api_key = view.kwargs.get("environment_api_key")
        with suppress(Environment.DoesNotExist):
            environment = Environment.objects.get(api_key=environment_api_key)

            if (
                view.action == "create"
                and request.data["environment"] != environment.id
            ):
                return False

            return request.user.has_environment_permission(
                action_permission_map.get(view.action), environment
            )
        return False

    def has_object_permission(self, request, view, obj):
        action_permission_map = {"retrieve": VIEW_ENVIRONMENT}

        return request.user.has_environment_permission(
            permission=action_permission_map.get(view.action, UPDATE_FEATURE_STATE),
            environment=obj.environment,
        )


class IdentityFeatureStatePermissions(EnvironmentFeatureStatePermissions):
    pass


class CreateSegmentOverridePermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        environment = get_object_or_404(
            Environment, api_key=view.kwargs["environment_api_key"]
        )

        # TODO: create dedicated permission for creating segment overrides
        return request.user.has_environment_permission(
            permission=UPDATE_FEATURE_STATE,
            environment=environment,
        )

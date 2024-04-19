from contextlib import suppress

from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet

from environments.models import Environment
from environments.permissions.constants import MANAGE_SEGMENT_OVERRIDES
from environments.permissions.constants import (
    TAG_SUPPORTED_PERMISSIONS as TAG_SUPPORTED_ENVIRONMENT_PERMISSIONS,
)
from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from features.models import Feature, FeatureState
from projects.models import Project
from projects.permissions import CREATE_FEATURE, DELETE_FEATURE
from projects.permissions import (
    TAG_SUPPORTED_PERMISSIONS as TAG_SUPPORTED_PROJECT_PERMISSIONS,
)
from projects.permissions import VIEW_PROJECT

ACTION_PERMISSIONS_MAP = {
    "retrieve": VIEW_PROJECT,
    "destroy": DELETE_FEATURE,
    "list": VIEW_PROJECT,
    "create": CREATE_FEATURE,
    "add_owners": CREATE_FEATURE,
    "remove_owners": CREATE_FEATURE,
    "add_group_owners": CREATE_FEATURE,
    "remove_group_owners": CREATE_FEATURE,
    "update": CREATE_FEATURE,
    "partial_update": CREATE_FEATURE,
}


class FeaturePermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        if view.detail:
            # handled by has_object_permission
            return True

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
            tag_ids = []
            required_permission = ACTION_PERMISSIONS_MAP.get(view.action)
            if required_permission in TAG_SUPPORTED_PROJECT_PERMISSIONS:
                tag_ids = list(obj.tags.values_list("id", flat=True))

            return request.user.has_project_permission(
                ACTION_PERMISSIONS_MAP[view.action], obj.project, tag_ids=tag_ids
            )

        if view.action == "segments":
            return request.user.is_project_admin(obj.project)

        return False


class FeatureStatePermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: GenericViewSet) -> bool:
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

                tag_ids = None

                if view.action == "list":
                    required_permission = VIEW_ENVIRONMENT
                elif (
                    view.action == "create"
                    and request.data.get("feature_segment") is not None
                ):
                    required_permission = MANAGE_SEGMENT_OVERRIDES
                else:
                    required_permission = UPDATE_FEATURE_STATE

                if required_permission in TAG_SUPPORTED_ENVIRONMENT_PERMISSIONS:
                    feature_id = request.data.get("feature")
                    feature = Feature.objects.get(id=feature_id)

                    tag_ids = list(feature.tags.values_list("id", flat=True))

                return request.user.has_environment_permission(
                    required_permission, environment, tag_ids=tag_ids
                )
            return False

        except (Environment.DoesNotExist, Feature.DoesNotExist):
            return False

    def has_object_permission(
        self, request: Request, view: GenericViewSet, obj: FeatureState
    ) -> bool:
        permission = (
            MANAGE_SEGMENT_OVERRIDES if obj.feature_segment_id else UPDATE_FEATURE_STATE
        )

        tag_ids = None
        if permission in TAG_SUPPORTED_ENVIRONMENT_PERMISSIONS:
            tag_ids = list(obj.feature.tags.values_list("id", flat=True))

        return request.user.has_environment_permission(
            permission, environment=obj.environment, tag_ids=tag_ids
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

        return request.user.has_environment_permission(
            permission=MANAGE_SEGMENT_OVERRIDES,
            environment=environment,
        )


class FeatureExternalResourcePermissions(FeaturePermissions):
    def has_object_permission(self, request, view, obj):
        if view.action == "destroy":
            return request.user.has_project_permission(
                CREATE_FEATURE, obj.feature.project
            )

        return request.user.has_project_permission(
            ACTION_PERMISSIONS_MAP[view.action], obj.feature.project
        )

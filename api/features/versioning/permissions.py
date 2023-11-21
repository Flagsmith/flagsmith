from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet

from environments.models import Environment
from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from features.models import FeatureState
from features.versioning.models import EnvironmentFeatureVersion


class EnvironmentFeatureVersionPermissions(BasePermission):
    def has_permission(self, request: Request, view: GenericViewSet) -> bool:
        if view.action == "list":
            # permissions for listing handled in view.get_queryset
            return True

        environment_pk = view.kwargs["environment_pk"]
        environment = Environment.objects.get(id=environment_pk)
        return request.user.has_environment_permission(
            permission=UPDATE_FEATURE_STATE, environment=environment
        )

    def has_object_permission(
        self, request: Request, view: GenericViewSet, obj: EnvironmentFeatureVersion
    ) -> bool:
        if view.action == "retrieve":
            # permissions for retrieving handled in view.get_queryset
            return True

        return request.user.has_environment_permission(
            permission=UPDATE_FEATURE_STATE, environment=obj.environment
        )


class EnvironmentFeatureVersionFeatureStatePermissions(BasePermission):
    def has_permission(self, request: Request, view: GenericViewSet) -> bool:
        environment_pk = view.kwargs["environment_pk"]
        environment = Environment.objects.get(id=environment_pk)

        if view.action == "list":
            return request.user.has_environment_permission(
                permission=VIEW_ENVIRONMENT, environment=environment
            )

        return request.user.has_environment_permission(
            permission=UPDATE_FEATURE_STATE, environment=environment
        )

    def has_object_permission(
        self, request: Request, view: GenericViewSet, obj: FeatureState
    ) -> bool:
        if view.action == "retrieve":
            return request.user.has_environment_permission(
                permission=VIEW_ENVIRONMENT, environment=obj.environment
            )

        return request.user.has_environment_permission(
            permission=UPDATE_FEATURE_STATE, environment=obj.environment
        )

from common.environments.permissions import (
    TAG_SUPPORTED_PERMISSIONS as TAG_SUPPORTED_ENVIRONMENT_PERMISSIONS,
)
from common.environments.permissions import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet

from environments.models import Environment
from features.models import Feature, FeatureState
from features.versioning.models import EnvironmentFeatureVersion


class EnvironmentFeatureVersionPermissions(BasePermission):
    def has_permission(self, request: Request, view: GenericViewSet) -> bool:  # type: ignore[override,type-arg]
        if view.action in ("list", "retrieve"):
            # permissions for listing and retrieving handled in view.get_queryset
            return True

        environment_pk = view.kwargs["environment_pk"]
        environment = Environment.objects.get(id=environment_pk)

        tag_ids = None
        required_permission = UPDATE_FEATURE_STATE

        if required_permission in TAG_SUPPORTED_ENVIRONMENT_PERMISSIONS:
            feature_id = view.kwargs["feature_pk"]
            feature = Feature.objects.get(id=feature_id, project=environment.project)
            tag_ids = list(feature.tags.values_list("id", flat=True))

        return request.user.has_environment_permission(  # type: ignore[union-attr]
            permission=required_permission,
            environment=environment,
            tag_ids=tag_ids,  # type: ignore[arg-type]
        )

    def has_object_permission(
        self,
        request: Request,
        view: GenericViewSet,  # type: ignore[override,type-arg]
        obj: EnvironmentFeatureVersion,  # noqa: E501
    ) -> bool:
        if view.action == "retrieve":
            # permissions for retrieving handled in view.get_queryset
            return True

        tag_ids = None
        required_permission = UPDATE_FEATURE_STATE

        if required_permission in TAG_SUPPORTED_ENVIRONMENT_PERMISSIONS:
            tag_ids = list(obj.feature.tags.values_list("id", flat=True))

        return request.user.has_environment_permission(  # type: ignore[union-attr]
            permission=required_permission,
            environment=obj.environment,
            tag_ids=tag_ids,  # type: ignore[arg-type]
        )


class EnvironmentFeatureVersionRetrievePermissions(BasePermission):
    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        return request.user.has_environment_permission(
            VIEW_ENVIRONMENT, obj.environment
        )


class EnvironmentFeatureVersionFeatureStatePermissions(BasePermission):
    def has_permission(self, request: Request, view: GenericViewSet) -> bool:  # type: ignore[override,type-arg]
        environment_pk = view.kwargs["environment_pk"]
        environment = Environment.objects.get(id=environment_pk)

        if view.action == "list":
            return request.user.has_environment_permission(  # type: ignore[union-attr]
                permission=VIEW_ENVIRONMENT, environment=environment
            )

        return request.user.has_environment_permission(  # type: ignore[union-attr]
            permission=UPDATE_FEATURE_STATE, environment=environment
        )

    def has_object_permission(
        self,
        request: Request,
        view: GenericViewSet,  # type: ignore[override,type-arg]
        obj: FeatureState,
    ) -> bool:
        if view.action == "retrieve":
            return request.user.has_environment_permission(  # type: ignore[union-attr]
                permission=VIEW_ENVIRONMENT,
                environment=obj.environment,  # type: ignore[arg-type]
            )

        return request.user.has_environment_permission(  # type: ignore[union-attr]
            permission=UPDATE_FEATURE_STATE,
            environment=obj.environment,  # type: ignore[arg-type]
        )

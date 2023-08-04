from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from environments.models import Environment
from environments.permissions.constants import VIEW_ENVIRONMENT
from features.models import Feature, FeatureState
from features.serializers import CreateSegmentOverrideFeatureStateSerializer
from features.versioning.exceptions import FeatureVersionDeleteError
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.permissions import (
    EnvironmentFeatureVersionFeatureStatePermissions,
    EnvironmentFeatureVersionPermissions,
)
from features.versioning.serializers import (
    EnvironmentFeatureVersionFeatureStateSerializer,
    EnvironmentFeatureVersionPublishSerializer,
    EnvironmentFeatureVersionSerializer,
)
from projects.permissions import VIEW_PROJECT


class EnvironmentFeatureVersionViewSet(
    GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
):
    serializer_class = EnvironmentFeatureVersionSerializer
    permission_classes = [IsAuthenticated, EnvironmentFeatureVersionPermissions]

    def get_serializer_class(self):
        match self.action:
            case "publish":
                return EnvironmentFeatureVersionPublishSerializer
            case _:
                return EnvironmentFeatureVersionSerializer

    def initial(self, request: Request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        feature = get_object_or_404(
            Feature.objects.filter(
                project__in=self.request.user.get_permitted_projects(VIEW_PROJECT)
            ),
            pk=self.kwargs["feature_pk"],
        )
        environment = get_object_or_404(
            self.request.user.get_permitted_environments(
                VIEW_ENVIRONMENT, project=feature.project
            ),
            pk=self.kwargs["environment_pk"],
        )

        request.feature = feature
        request.environment = environment

    def get_queryset(self):
        return EnvironmentFeatureVersion.objects.filter(
            environment=self.request.environment, feature_id=self.request.feature
        )

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(
            environment=self.request.environment, feature=self.request.feature
        )

    def perform_destroy(self, instance: EnvironmentFeatureVersion) -> None:
        if instance.is_live:
            raise FeatureVersionDeleteError("Cannot delete a live version.")

        super().perform_destroy(instance)

    @action(detail=True, methods=["POST"])
    def publish(self, request: Request, **kwargs) -> Response:
        ef_version = self.get_object()
        serializer = self.get_serializer(data=request.data, instance=ef_version)
        serializer.is_valid(raise_exception=True)
        serializer.save(published_by=request.user)
        return Response(serializer.data)


class EnvironmentFeatureVersionFeatureStatesViewSet(
    GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
):
    serializer_class = EnvironmentFeatureVersionFeatureStateSerializer
    permission_classes = [
        IsAuthenticated,
        EnvironmentFeatureVersionFeatureStatePermissions,
    ]
    pagination_class = None

    def get_queryset(self):
        environment_feature_version_sha = self.kwargs["environment_feature_version_pk"]

        return FeatureState.objects.filter(
            environment=self.request.environment,
            feature=self.request.feature,
            environment_feature_version_id=environment_feature_version_sha,
        )

    def initial(self, request: Request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        environment_feature_version = get_object_or_404(
            EnvironmentFeatureVersion, sha=self.kwargs["environment_feature_version_pk"]
        )
        if self.action != "list" and environment_feature_version.published is True:
            raise FeatureVersionDeleteError("Cannot modify published version.")

        # patch the objects onto the request
        request.environment_feature_version = environment_feature_version
        request.environment = get_object_or_404(
            Environment, pk=self.kwargs["environment_pk"]
        )
        request.feature = get_object_or_404(Feature, pk=self.kwargs["feature_pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["environment"] = self.request.environment
        context["feature"] = self.request.feature
        return context

    def perform_create(self, serializer: CreateSegmentOverrideFeatureStateSerializer):
        serializer.save(
            feature=self.request.feature,
            environment=self.request.environment,
            environment_feature_version=self.request.environment_feature_version,
        )

    def perform_update(self, serializer: CreateSegmentOverrideFeatureStateSerializer):
        serializer.save(
            feature=self.request.feature,
            environment=self.request.environment,
            environment_feature_version=self.request.environment_feature_version,
        )

    def perform_destroy(self, instance):
        if instance.feature_segment is None and instance.identity is None:
            raise FeatureVersionDeleteError(
                "Cannot delete environment default feature state."
            )
        super().perform_destroy(instance)

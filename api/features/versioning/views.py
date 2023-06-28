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
from features.models import Feature, FeatureState
from features.serializers import CreateSegmentOverrideFeatureStateSerializer
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.serializers import EnvironmentFeatureVersionSerializer


class EnvironmentFeatureVersionViewSet(
    GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
):
    serializer_class = EnvironmentFeatureVersionSerializer
    permission_classes = [IsAuthenticated]  # TODO

    def initial(self, request: Request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        # TODO: permissions to verify user has access to environment / feature
        self.environment = get_object_or_404(
            Environment, pk=self.kwargs["environment_pk"]
        )
        self.feature = get_object_or_404(Feature, pk=self.kwargs["feature_pk"])

    def get_queryset(self):
        return EnvironmentFeatureVersion.objects.filter(
            environment=self.environment, feature_id=self.feature
        )

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(environment=self.environment, feature=self.feature)

    def perform_update(self, serializer: Serializer) -> None:
        serializer.save(environment=self.environment, feature=self.feature)

    @action(detail=True, methods=["POST"])
    def publish(self, request: Request, **kwargs) -> Response:
        ef_version = self.get_object()
        ef_version.publish()
        ef_version.save()
        return Response(self.get_serializer(instance=ef_version).data)


class EnvironmentFeatureVersionFeatureStatesViewSet(
    GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,  # TODO: prevent deletion, update for published versions?
):
    serializer_class = CreateSegmentOverrideFeatureStateSerializer
    permission_classes = [IsAuthenticated]  # TODO
    pagination_class = None

    def get_queryset(self):
        environment_feature_version_sha = self.kwargs["environment_feature_version_pk"]

        return FeatureState.objects.filter(
            environment=self.environment,
            feature=self.feature,
            environment_feature_version_id=environment_feature_version_sha,
        )

    def initial(self, request: Request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.environment = get_object_or_404(
            Environment, pk=self.kwargs["environment_pk"]
        )
        self.feature = get_object_or_404(Feature, pk=self.kwargs["feature_pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["environment"] = self.environment
        context["feature"] = self.feature
        return context

    def perform_create(self, serializer: CreateSegmentOverrideFeatureStateSerializer):
        serializer.save(feature=self.feature, environment=self.environment)

    def perform_update(self, serializer: CreateSegmentOverrideFeatureStateSerializer):
        serializer.save(feature=self.feature, environment=self.environment)

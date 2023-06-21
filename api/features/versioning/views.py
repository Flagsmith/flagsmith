from django.shortcuts import get_object_or_404
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from environments.models import Environment
from features.models import Feature, FeatureState
from features.serializers import WritableNestedFeatureStateSerializer
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

    def get_queryset(self):
        environment_pk = self.kwargs["environment_pk"]
        feature_pk = self.kwargs["feature_pk"]

        return EnvironmentFeatureVersion.objects.filter(
            environment_id=environment_pk, feature_id=feature_pk
        )

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(
            environment=self._get_environment(), feature=self._get_feature()
        )

    def perform_update(self, serializer: Serializer) -> None:
        serializer.save(
            environment=self._get_environment(), feature=self._get_feature()
        )

    def _get_environment(self) -> Environment:
        # TODO: use permissions to ensure only user permitted environments
        return get_object_or_404(Environment, pk=self.kwargs["environment_pk"])

    def _get_feature(self) -> Feature:
        # TODO: use permissions to ensure only user permitted features
        return get_object_or_404(Feature, pk=self.kwargs["feature_pk"])


class EnvironmentFeatureVersionFeatureStatesViewSet(
    GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,  # TODO: prevent deletion, update for published versions?
):
    serializer_class = WritableNestedFeatureStateSerializer
    permission_classes = [IsAuthenticated]  # TODO
    pagination_class = None

    def get_queryset(self):
        environment_feature_version_sha = self.kwargs["environment_feature_version_pk"]

        return FeatureState.objects.filter(
            environment_feature_version_id=environment_feature_version_sha,
        )

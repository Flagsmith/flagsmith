from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    UpdateModelMixin,
)
from rest_framework.viewsets import GenericViewSet

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

    def get_queryset(self):
        environment_pk = self.kwargs["environment_pk"]
        feature_pk = self.kwargs["feature_pk"]

        return EnvironmentFeatureVersion.objects.filter(
            environment_id=environment_pk, feature_id=feature_pk
        )

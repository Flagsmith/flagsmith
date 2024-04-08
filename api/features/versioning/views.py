from django.db.models import BooleanField, ExpressionWrapper, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
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
    EnvironmentFeatureVersionQuerySerializer,
    EnvironmentFeatureVersionSerializer,
)
from projects.permissions import VIEW_PROJECT
from users.models import FFAdminUser


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        query_serializer=EnvironmentFeatureVersionQuerySerializer()
    ),
)
class EnvironmentFeatureVersionViewSet(
    GenericViewSet,
    ListModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
):
    serializer_class = EnvironmentFeatureVersionSerializer
    permission_classes = [IsAuthenticated, EnvironmentFeatureVersionPermissions]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # populated during the request to use across multiple view methods
        self.feature = None
        self.environment = None

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

        self.feature = feature
        self.environment = environment

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return EnvironmentFeatureVersion.objects.none()

        queryset = EnvironmentFeatureVersion.objects.filter(
            environment=self.environment, feature_id=self.feature
        )

        query_serializer = EnvironmentFeatureVersionQuerySerializer(
            data=self.request.query_params
        )
        query_serializer.is_valid(raise_exception=True)

        if (is_live := query_serializer.validated_data.get("is_live")) is not None:
            queryset = queryset.annotate(
                _is_live=ExpressionWrapper(
                    Q(published_at__isnull=False, live_from__lte=timezone.now()),
                    output_field=BooleanField(),
                )
            )
            queryset = queryset.filter(_is_live=is_live)

        return queryset

    def perform_create(self, serializer: Serializer) -> None:
        created_by = None
        if isinstance(self.request.user, FFAdminUser):
            created_by = self.request.user
        serializer.save(
            environment=self.environment, feature=self.feature, created_by=created_by
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # populated during the request to use across multiple view methods
        self.feature = None
        self.environment = None
        self.environment_feature_version = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return FeatureState.objects.none()

        environment_feature_version_uuid = self.kwargs["environment_feature_version_pk"]

        return FeatureState.objects.filter(
            environment=self.environment,
            feature=self.feature,
            environment_feature_version_id=environment_feature_version_uuid,
        )

    def initial(self, request: Request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        environment_feature_version = get_object_or_404(
            EnvironmentFeatureVersion,
            uuid=self.kwargs["environment_feature_version_pk"],
        )
        if self.action != "list" and environment_feature_version.published is True:
            raise FeatureVersionDeleteError("Cannot modify published version.")

        # patch the objects onto the view to use in other methods
        self.environment_feature_version = environment_feature_version
        self.environment = get_object_or_404(
            Environment, pk=self.kwargs["environment_pk"]
        )
        self.feature = get_object_or_404(Feature, pk=self.kwargs["feature_pk"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["environment"] = self.environment
        context["feature"] = self.feature
        context["environment_feature_version"] = self.environment_feature_version
        return context

    def perform_create(self, serializer: CreateSegmentOverrideFeatureStateSerializer):
        serializer.save(
            feature=self.feature,
            environment=self.environment,
            environment_feature_version=self.environment_feature_version,
        )

    def perform_update(self, serializer: CreateSegmentOverrideFeatureStateSerializer):
        serializer.save(
            feature=self.feature,
            environment=self.environment,
            environment_feature_version=self.environment_feature_version,
        )

    def perform_destroy(self, instance):
        if instance.feature_segment is None and instance.identity is None:
            raise FeatureVersionDeleteError(
                "Cannot delete environment default feature state."
            )
        super().perform_destroy(instance)

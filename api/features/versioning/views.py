from datetime import timedelta

from common.environments.permissions import (  # type: ignore[import-untyped]
    VIEW_ENVIRONMENT,
)
from common.projects.permissions import VIEW_PROJECT  # type: ignore[import-untyped]
from django.db.models import BooleanField, ExpressionWrapper, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView
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

from app.pagination import CustomPagination
from environments.models import Environment
from features.models import Feature, FeatureState
from features.serializers import (
    CustomCreateSegmentOverrideFeatureStateSerializer,
)
from features.versioning.exceptions import FeatureVersionDeleteError
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.permissions import (
    EnvironmentFeatureVersionFeatureStatePermissions,
    EnvironmentFeatureVersionPermissions,
    EnvironmentFeatureVersionRetrievePermissions,
)
from features.versioning.serializers import (
    CustomEnvironmentFeatureVersionFeatureStateSerializer,
    EnvironmentFeatureVersionCreateSerializer,
    EnvironmentFeatureVersionPublishSerializer,
    EnvironmentFeatureVersionQuerySerializer,
    EnvironmentFeatureVersionRetrieveSerializer,
    EnvironmentFeatureVersionSerializer,
)
from users.models import FFAdminUser


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        query_serializer=EnvironmentFeatureVersionQuerySerializer()
    ),
)
class EnvironmentFeatureVersionViewSet(
    GenericViewSet,  # type: ignore[type-arg]
    ListModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
):
    permission_classes = [IsAuthenticated, EnvironmentFeatureVersionPermissions]
    pagination_class = CustomPagination

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)

        # populated during the request to use across multiple view methods
        self.feature = None
        self.environment = None

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        match self.action:
            case "publish":
                return EnvironmentFeatureVersionPublishSerializer
            case "retrieve":
                return EnvironmentFeatureVersionRetrieveSerializer
            case "create":
                return EnvironmentFeatureVersionCreateSerializer
            case _:
                return EnvironmentFeatureVersionSerializer

    def initial(self, request: Request, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().initial(request, *args, **kwargs)

        feature = get_object_or_404(
            Feature.objects.filter(
                project__in=self.request.user.get_permitted_projects(VIEW_PROJECT)  # type: ignore[union-attr]
            ),
            pk=self.kwargs["feature_pk"],
        )
        environment = get_object_or_404(
            self.request.user.get_permitted_environments(  # type: ignore[union-attr]
                VIEW_ENVIRONMENT, project=feature.project
            ),
            pk=self.kwargs["environment_pk"],
        )

        self.feature = feature
        self.environment = environment

    def get_queryset(self):  # type: ignore[no-untyped-def]
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

        if self.action == "list":
            queryset = self._apply_visibility_limits(queryset)

        return queryset

    def perform_create(self, serializer: Serializer) -> None:  # type: ignore[override,type-arg]
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
    def publish(self, request: Request, **kwargs) -> Response:  # type: ignore[no-untyped-def]
        ef_version = self.get_object()
        serializer = self.get_serializer(data=request.data, instance=ef_version)
        serializer.is_valid(raise_exception=True)
        serializer.save(published_by=request.user)
        return Response(serializer.data)

    def _apply_visibility_limits(self, queryset: QuerySet) -> QuerySet:  # type: ignore[type-arg]
        """
        Filter the given queryset by the visibility limits enforced
        by the given organisation's subscription.
        """
        subscription = self.environment.project.organisation.subscription  # type: ignore[union-attr]
        subscription_metadata = subscription.get_subscription_metadata()
        if (
            subscription_metadata
            and (
                version_limit_days
                := subscription_metadata.feature_history_visibility_days
            )
            is not None
        ):
            limited_queryset = queryset.filter(
                Q(live_from__gte=timezone.now() - timedelta(days=version_limit_days))
                | Q(live_from__isnull=True)
            )
            if not limited_queryset.exists():
                # If there are no versions in the visible time frame for the
                # given user, we still need to make that we return the live
                # version, which will be the first one in the original qs.
                return queryset[:1]
            return limited_queryset
        return queryset


class EnvironmentFeatureVersionRetrieveAPIView(RetrieveAPIView):  # type: ignore[type-arg]
    """
    This is an additional endpoint to retrieve a specific version without needing
    to provide the environment or feature as part of the URL.
    """

    permission_classes = [
        IsAuthenticated,
        EnvironmentFeatureVersionRetrievePermissions,
    ]
    serializer_class = EnvironmentFeatureVersionRetrieveSerializer

    def get_queryset(self):  # type: ignore[no-untyped-def]
        return EnvironmentFeatureVersion.objects.all()


class EnvironmentFeatureVersionFeatureStatesViewSet(
    GenericViewSet,  # type: ignore[type-arg]
    ListModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
):
    serializer_class = CustomEnvironmentFeatureVersionFeatureStateSerializer
    permission_classes = [
        IsAuthenticated,
        EnvironmentFeatureVersionFeatureStatePermissions,
    ]
    pagination_class = None

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)

        # populated during the request to use across multiple view methods
        self.feature = None
        self.environment = None
        self.environment_feature_version = None

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return FeatureState.objects.none()

        environment_feature_version_uuid = self.kwargs["environment_feature_version_pk"]

        return FeatureState.objects.filter(
            environment=self.environment,
            feature=self.feature,
            environment_feature_version_id=environment_feature_version_uuid,
        )

    def initial(self, request: Request, *args, **kwargs):  # type: ignore[no-untyped-def]
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

    def get_serializer_context(self):  # type: ignore[no-untyped-def]
        context = super().get_serializer_context()
        context["environment"] = self.environment
        context["feature"] = self.feature
        context["environment_feature_version"] = self.environment_feature_version
        return context

    def perform_create(
        self,
        serializer: CustomCreateSegmentOverrideFeatureStateSerializer,  # type: ignore[override]
    ) -> None:
        serializer.save(
            feature=self.feature,
            environment=self.environment,
            environment_feature_version=self.environment_feature_version,
        )

    def perform_update(
        self,
        serializer: CustomCreateSegmentOverrideFeatureStateSerializer,  # type: ignore[override]
    ) -> None:
        serializer.save(
            feature=self.feature,
            environment=self.environment,
            environment_feature_version=self.environment_feature_version,
        )

    def perform_destroy(self, instance) -> None:  # type: ignore[no-untyped-def]
        if instance.feature_segment is None and instance.identity is None:
            raise FeatureVersionDeleteError(
                "Cannot delete environment default feature state."
            )
        super().perform_destroy(instance)

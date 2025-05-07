import logging
from typing import Any
from common.environments.permissions import (
    TAG_SUPPORTED_PERMISSIONS,
    VIEW_ENVIRONMENT,
)
from django.db.models import Count, Q
from django.utils.decorators import method_decorator
from drf_yasg import openapi  # type: ignore[import-untyped]
from drf_yasg.utils import no_body, swagger_auto_schema  # type: ignore[import-untyped]
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from metrics.types import EnvMetricsPayload

from environments.permissions.permissions import (
    EnvironmentAdminPermission,
    EnvironmentPermissions,
    NestedEnvironmentPermissions,
)
from environments.sdk.schemas import SDKEnvironmentDocumentModel
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import (
    disable_v2_versioning,
    enable_v2_versioning,
)
from metrics.serializers import EnvironmentMetricsSerializer
from metrics.views import BaseMetricsViewSet
from permissions.permissions_calculator import get_environment_permission_data
from permissions.serializers import (
    PermissionModelSerializer,
    UserObjectPermissionsSerializer,
)
from projects.models import Project
from webhooks.mixins import TriggerSampleWebhookMixin
from webhooks.webhooks import WebhookType

from .identities.traits.models import Trait
from .identities.traits.serializers import (
    DeleteAllTraitKeysSerializer,
    TraitKeysSerializer,
)
from .models import Environment, EnvironmentAPIKey, Webhook
from .permissions.models import (
    EnvironmentPermissionModel,
    UserEnvironmentPermission,
)
from .serializers import (
    CloneEnvironmentSerializer,
    CreateUpdateEnvironmentSerializer,
    EnvironmentAPIKeySerializer,
    EnvironmentRetrieveSerializerWithMetadata,
    EnvironmentSerializerWithMetadata,
    WebhookSerializer,
)

logger = logging.getLogger(__name__)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "project",
                openapi.IN_QUERY,
                "ID of the project to filter by.",
                required=False,
                type=openapi.TYPE_INTEGER,
            )
        ]
    ),
)
class EnvironmentViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    lookup_field = "api_key"
    permission_classes = [EnvironmentPermissions]

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if self.action == "trait_keys":
            return TraitKeysSerializer
        if self.action == "delete_traits":
            return DeleteAllTraitKeysSerializer
        if self.action == "clone":
            return CloneEnvironmentSerializer
        if self.action == "retrieve":
            return EnvironmentRetrieveSerializerWithMetadata
        elif self.action in ("create", "update", "partial_update"):
            return CreateUpdateEnvironmentSerializer
        return EnvironmentSerializerWithMetadata

    def get_serializer_context(self):  # type: ignore[no-untyped-def]
        context = super(EnvironmentViewSet, self).get_serializer_context()
        if self.kwargs.get("api_key"):
            context["environment"] = self.get_object()
        return context

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if self.action == "list":
            project_id = self.request.query_params.get(
                "project"
            ) or self.request.data.get("project")

            try:
                project = Project.objects.get(id=project_id)
            except Project.DoesNotExist:
                raise ValidationError("Invalid or missing value for project parameter.")

            return self.request.user.get_permitted_environments(  # type: ignore[union-attr]
                "VIEW_ENVIRONMENT", project=project, prefetch_metadata=True
            )

        # Permission class handles validation of permissions for other actions
        queryset = Environment.objects.all()

        if self.action == "retrieve":
            # Since we don't have the environment at this stage, we would need to query the database
            # regardless, so it seems worthwhile to just query the database for the latest versions
            # and use their existence as a proxy to whether v2 feature versioning is enabled.
            latest_versions = EnvironmentFeatureVersion.objects.get_latest_versions_by_environment_api_key(
                environment_api_key=self.kwargs["api_key"]
            )
            if latest_versions:
                # if there are latest versions (and hence v2 feature versioning is enabled), then
                # we need to ensure that we're only counting the feature segments for those
                # latest versions against the limits.
                queryset = queryset.annotate(
                    total_segment_overrides=Count(
                        "feature_segments",
                        filter=Q(
                            feature_segments__environment_feature_version__in=latest_versions
                        ),
                    )
                )
            else:
                queryset = queryset.annotate(
                    total_segment_overrides=Count("feature_segments")
                )

        return queryset

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        environment = serializer.save()
        if getattr(self.request.user, "is_master_api_key_user", False) is False:
            UserEnvironmentPermission.objects.create(  # type: ignore[misc]
                user=self.request.user, environment=environment, admin=True
            )

    @action(
        detail=False,
        url_path=r"get-by-uuid/(?P<uuid>[0-9a-f-]+)",
        methods=["get"],
    )
    def get_by_uuid(self, request, uuid):  # type: ignore[no-untyped-def]
        qs = self.get_queryset()  # type: ignore[no-untyped-call]
        environment = get_object_or_404(qs, uuid=uuid)
        if not request.user.has_environment_permission(VIEW_ENVIRONMENT, environment):
            raise PermissionDenied()

        serializer = self.get_serializer(environment)
        return Response(serializer.data)

    @action(detail=True, methods=["GET"], url_path="trait-keys")
    def trait_keys(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        keys = [
            trait_key
            for trait_key in Trait.objects.filter(
                identity__environment=self.get_object()
            )
            .order_by()
            .values_list("trait_key", flat=True)
            .distinct()
        ]

        data = {"keys": keys}

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Couldn't get trait keys"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["POST"])
    def clone(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        clone = serializer.save(source_env=self.get_object())

        if getattr(request.user, "is_master_api_key_user", False) is False:
            UserEnvironmentPermission.objects.create(  # type: ignore[misc]
                user=self.request.user, environment=clone, admin=True
            )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"], url_path="delete-traits")
    def delete_traits(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.delete()  # type: ignore[attr-defined]
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Couldn't delete trait keys."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(responses={200: PermissionModelSerializer(many=True)})
    @action(detail=False, methods=["GET"])
    def permissions(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return Response(
            PermissionModelSerializer(
                instance=EnvironmentPermissionModel.objects.all(),
                many=True,
                context={"tag_supported_permissions": TAG_SUPPORTED_PERMISSIONS},
            ).data
        )

    @swagger_auto_schema(responses={200: UserObjectPermissionsSerializer})
    @action(
        detail=True,
        methods=["GET"],
        url_path="my-permissions",
        url_name="my-permissions",
    )
    def user_permissions(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        if getattr(request.user, "is_master_api_key_user", False) is True:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "detail": "This endpoint can only be used with a user and not Master API Key"
                },
            )

        environment = self.get_object()

        permission_data = get_environment_permission_data(
            environment=environment, user=request.user
        )
        serializer = UserObjectPermissionsSerializer(instance=permission_data)
        return Response(serializer.data)

    @swagger_auto_schema(responses={200: SDKEnvironmentDocumentModel})  # type: ignore[misc]
    @action(detail=True, methods=["GET"], url_path="document")
    def get_document(self, request, api_key: str):  # type: ignore[no-untyped-def]
        environment = (
            self.get_object()
        )  # use get_object to ensure permissions check is performed
        return Response(Environment.get_environment_document(environment.api_key))

    @swagger_auto_schema(request_body=no_body, responses={202: ""})  # type: ignore[misc]
    @action(detail=True, methods=["POST"], url_path="enable-v2-versioning")
    def enable_v2_versioning(self, request: Request, api_key: str) -> Response:
        environment = self.get_object()
        if environment.use_v2_feature_versioning is True:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": "Environment already using v2 versioning."},
            )
        enable_v2_versioning.delay(kwargs={"environment_id": environment.id})
        return Response(status=status.HTTP_202_ACCEPTED)

    @swagger_auto_schema(request_body=no_body, responses={202: ""})  # type: ignore[misc]
    @action(detail=True, methods=["POST"], url_path="disable-v2-versioning")
    def disable_v2_versioning(self, request: Request, api_key: str) -> Response:
        environment = self.get_object()
        if environment.use_v2_feature_versioning is False:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"detail": "Environment is not using v2 versioning."},
            )
        disable_v2_versioning.delay(kwargs={"environment_id": environment.id})
        return Response(status=status.HTTP_202_ACCEPTED)


class NestedEnvironmentViewSet(viewsets.GenericViewSet):  # type: ignore[type-arg]
    model_class = None
    webhook_type = WebhookType.ENVIRONMENT

    def get_queryset(self):  # type: ignore[no-untyped-def]
        return self.model_class.objects.filter(  # type: ignore[attr-defined]
            environment__api_key=self.kwargs.get("environment_api_key")
        )

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        serializer.save(environment=self._get_environment())  # type: ignore[no-untyped-call]

    def perform_update(self, serializer):  # type: ignore[no-untyped-def]
        serializer.save(environment=self._get_environment())  # type: ignore[no-untyped-call]

    def _get_environment(self):  # type: ignore[no-untyped-def]
        return Environment.objects.get(api_key=self.kwargs.get("environment_api_key"))


class WebhookViewSet(
    NestedEnvironmentViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    TriggerSampleWebhookMixin,
):
    serializer_class = WebhookSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, NestedEnvironmentPermissions]
    model_class = Webhook  # type: ignore[assignment]

    webhook_type = WebhookType.ENVIRONMENT  # type: ignore[assignment]


class EnvironmentAPIKeyViewSet(
    NestedEnvironmentViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = EnvironmentAPIKeySerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, EnvironmentAdminPermission]
    model_class = EnvironmentAPIKey  # type: ignore[assignment]


class EnvironmentMetricsViewSet(NestedEnvironmentViewSet, BaseMetricsViewSet):
    model_class = Environment  # type: ignore[assignment]
    lookup_url_kwarg = "environment_api_key"
    serializer_class = EnvironmentMetricsSerializer

    def get_metrics(self, environment: Environment) -> EnvMetricsPayload:
        is_workflows_enabled = environment.change_requests_enabled
        return environment.get_metrics_payload(with_workflows=is_workflows_enabled)

    @swagger_auto_schema(  # type: ignore[misc]
        operation_description="Get metrics for this environment.",
        responses={200: openapi.Response("Metrics", EnvironmentMetricsSerializer)},
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().list(request, *args, **kwargs)

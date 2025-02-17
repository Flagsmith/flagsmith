import typing

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.request import Request
from rest_framework.response import Response

from features.feature_health.models import (
    FeatureHealthEvent,
    FeatureHealthProvider,
)
from features.feature_health.providers.services import (
    get_provider_from_webhook_path,
)
from features.feature_health.serializers import (
    CreateFeatureHealthProviderSerializer,
    FeatureHealthEventSerializer,
    FeatureHealthProviderSerializer,
)
from features.feature_health.services import (
    create_feature_health_event_from_provider,
)
from projects.models import Project
from projects.permissions import NestedProjectPermissions
from users.models import FFAdminUser


class FeatureHealthEventViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet,  # type: ignore[type-arg]
):
    serializer_class = FeatureHealthEventSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = FeatureHealthEvent

    def get_permissions(self) -> list[BasePermission]:
        return [NestedProjectPermissions()]

    def get_queryset(self) -> QuerySet[FeatureHealthProvider]:
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()

        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        return self.model_class.objects.get_latest_by_project(project)


class FeatureHealthProviderViewSet(
    mixins.DestroyModelMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,  # type: ignore[type-arg]
):
    serializer_class = FeatureHealthProviderSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = FeatureHealthProvider
    lookup_field = "name"

    def get_permissions(self) -> list[BasePermission]:
        return [NestedProjectPermissions()]

    def get_queryset(self) -> QuerySet[FeatureHealthProvider]:
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()

        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        return self.model_class.objects.filter(project=project)

    def get_object(self) -> FeatureHealthProvider:
        return get_object_or_404(  # type: ignore[no-any-return]
            self.model_class.objects,
            project_id=self.kwargs["project_pk"],
            name__iexact=self.kwargs["name"],
        )

    @swagger_auto_schema(  # type: ignore[misc]
        request_body=CreateFeatureHealthProviderSerializer,
        responses={status.HTTP_201_CREATED: FeatureHealthProviderSerializer()},
    )
    def create(self, request: Request, *args, **kwargs) -> Response:  # type: ignore[no-untyped-def]
        request_serializer = CreateFeatureHealthProviderSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])

        created_by = None
        if isinstance(self.request.user, FFAdminUser):
            created_by = self.request.user

        instance = self.model_class.objects.create(
            project=project,
            name=request_serializer.validated_data["name"],
            created_by=created_by,
        )

        serializer = FeatureHealthProviderSerializer(
            instance,
            context={"request": request},
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


@api_view(["POST"])  # type: ignore[arg-type]
@permission_classes([AllowAny])
def feature_health_webhook(request: Request, **kwargs: typing.Any) -> Response:
    path = kwargs["path"]
    if not (provider := get_provider_from_webhook_path(path)):
        return Response(status=status.HTTP_404_NOT_FOUND)
    payload = request.body.decode("utf-8")
    if create_feature_health_event_from_provider(provider=provider, payload=payload):
        return Response(status=status.HTTP_200_OK)
    return Response(status=status.HTTP_400_BAD_REQUEST)

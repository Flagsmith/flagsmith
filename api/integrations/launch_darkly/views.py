from common.projects.permissions import (  # type: ignore[import-untyped]
    CREATE_ENVIRONMENT,
    VIEW_PROJECT,
)
from django.db.models import QuerySet
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response

from integrations.launch_darkly.models import LaunchDarklyImportRequest
from integrations.launch_darkly.serializers import (
    CreateLaunchDarklyImportRequestSerializer,
    LaunchDarklyImportRequestSerializer,
)
from integrations.launch_darkly.services import create_import_request
from integrations.launch_darkly.tasks import (
    process_launch_darkly_import_request,
)
from projects.models import Project
from projects.permissions import NestedProjectPermissions


class LaunchDarklyImportRequestViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,  # type: ignore[type-arg]
):
    serializer_class = LaunchDarklyImportRequestSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = LaunchDarklyImportRequest

    def get_permissions(self) -> list[BasePermission]:
        return [
            NestedProjectPermissions(
                action_permission_map={
                    "retrieve": VIEW_PROJECT,
                    "create": CREATE_ENVIRONMENT,
                }
            ),
        ]

    def get_queryset(self) -> QuerySet[LaunchDarklyImportRequest]:
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()  # type: ignore[no-any-return]

        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])
        return self.model_class.objects.filter(project=project)  # type: ignore[no-any-return]

    @swagger_auto_schema(  # type: ignore[misc]
        request_body=CreateLaunchDarklyImportRequestSerializer,
        responses={status.HTTP_201_CREATED: LaunchDarklyImportRequestSerializer()},
    )
    def create(self, request: Request, *args, **kwargs) -> Response:  # type: ignore[no-untyped-def]
        request_serializer = CreateLaunchDarklyImportRequestSerializer(
            data=request.data
        )
        request_serializer.is_valid(raise_exception=True)

        project = get_object_or_404(Project, pk=self.kwargs["project_pk"])

        try:
            instance = create_import_request(
                project=project,
                user=self.request.user,  # type: ignore[arg-type]
                ld_token=request_serializer.validated_data["token"],
                ld_project_key=request_serializer.validated_data["project_key"],
            )
        except IntegrityError:
            raise ValidationError(
                "Existing import already in progress for this project"
            )

        process_launch_darkly_import_request.delay(
            kwargs={"import_request_id": instance.id}
        )

        serializer = LaunchDarklyImportRequestSerializer(instance)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

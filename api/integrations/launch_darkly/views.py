from django.db.models import QuerySet
from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
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
from projects.permissions import CREATE_ENVIRONMENT, VIEW_PROJECT


class LaunchDarklyImportRequestViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = LaunchDarklyImportRequestSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = LaunchDarklyImportRequest

    def get_queryset(self) -> QuerySet[LaunchDarklyImportRequest]:
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()

        project = get_object_or_404(
            self.request.user.get_permitted_projects(VIEW_PROJECT),
            pk=self.kwargs["project_pk"],
        )
        return self.model_class.objects.filter(project=project)

    @swagger_auto_schema(
        request_body=CreateLaunchDarklyImportRequestSerializer,
        responses={status.HTTP_201_CREATED: LaunchDarklyImportRequestSerializer()},
    )
    def create(self, request: Request, *args, **kwargs) -> Response:
        request_serializer = CreateLaunchDarklyImportRequestSerializer(
            data=request.data
        )
        request_serializer.is_valid(raise_exception=True)

        project = get_object_or_404(
            self.request.user.get_permitted_projects(CREATE_ENVIRONMENT),
            pk=self.kwargs["project_pk"],
        )

        try:
            instance = create_import_request(
                project=project,
                user=self.request.user,
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

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from environments.dynamodb.migrator import IdentityMigrator
from environments.identities.models import Identity
from environments.serializers import EnvironmentSerializerLight
from permissions.permissions_calculator import get_project_permission_data
from permissions.serializers import (
    PermissionModelSerializer,
    UserObjectPermissionsSerializer,
)
from projects.exceptions import (
    DynamoNotEnabledError,
    ProjectMigrationError,
    ProjectTooLargeError,
    TooManyIdentitiesError,
)
from projects.models import (
    Project,
    ProjectPermissionModel,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from projects.permissions import (
    VIEW_PROJECT,
    IsProjectAdmin,
    ProjectPermissions,
)
from projects.serializers import (
    CreateUpdateUserPermissionGroupProjectPermissionSerializer,
    CreateUpdateUserProjectPermissionSerializer,
    ListUserPermissionGroupProjectPermissionSerializer,
    ListUserProjectPermissionSerializer,
    ProjectListSerializer,
    ProjectRetrieveSerializer,
    ProjectUpdateOrCreateSerializer,
)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "organisation",
                openapi.IN_QUERY,
                "ID of the organisation to filter by.",
                required=False,
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "uuid",
                openapi.IN_QUERY,
                "uuid of the project to filter by.",
                required=False,
                type=openapi.TYPE_STRING,
            ),
        ]
    ),
)
class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [ProjectPermissions]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProjectRetrieveSerializer
        elif self.action in ("create", "update", "partial_update"):
            return ProjectUpdateOrCreateSerializer
        return ProjectListSerializer

    pagination_class = None

    def get_serializer_context(self):
        return super().get_serializer_context()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()

        queryset = self.request.user.get_permitted_projects(permission_key=VIEW_PROJECT)

        organisation_id = self.request.query_params.get("organisation")
        if organisation_id:
            queryset = queryset.filter(organisation__id=organisation_id)

        project_uuid = self.request.query_params.get("uuid")
        if project_uuid:
            queryset = queryset.filter(uuid=project_uuid)

        return queryset

    def perform_create(self, serializer):
        project = serializer.save()
        if getattr(self.request.user, "is_master_api_key_user", False) is False:
            UserProjectPermission.objects.create(
                user=self.request.user, project=project, admin=True
            )

    @action(
        detail=False,
        url_path=r"get-by-uuid/(?P<uuid>[0-9a-f-]+)",
        methods=["get"],
    )
    def get_by_uuid(self, request, uuid):
        qs = self.get_queryset()
        project = get_object_or_404(qs, uuid=uuid)
        serializer = self.get_serializer(project)
        return Response(serializer.data)

    @action(detail=True)
    def environments(self, request, pk):
        project = self.get_object()
        environments = project.environments.all()
        return Response(EnvironmentSerializerLight(environments, many=True).data)

    @swagger_auto_schema(
        responses={200: PermissionModelSerializer}, request_body=no_body
    )
    @action(detail=False, methods=["GET"])
    def permissions(self, *args, **kwargs):
        return Response(
            PermissionModelSerializer(
                instance=ProjectPermissionModel.objects.all(), many=True
            ).data
        )

    @swagger_auto_schema(responses={200: UserObjectPermissionsSerializer()})
    @action(
        detail=True,
        methods=["GET"],
        url_path="my-permissions",
        url_name="my-permissions",
    )
    def user_permissions(self, request: Request, pk: int = None):
        if getattr(request.user, "is_master_api_key_user", False) is True:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "detail": "This endpoint can only be used with a user and not Master API Key"
                },
            )
        permission_data = get_project_permission_data(pk, user_id=request.user.id)
        serializer = UserObjectPermissionsSerializer(instance=permission_data)
        return Response(serializer.data)

    @swagger_auto_schema(
        responses={202: "Migration event generated"}, request_body=no_body
    )
    @action(
        detail=True,
        methods=["POST"],
        url_path="migrate-to-edge",
    )
    def migrate_to_edge(self, request: Request, pk: int = None):
        if not settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
            raise DynamoNotEnabledError()

        project = self.get_object()
        if project.is_too_large:
            raise ProjectTooLargeError()

        identity_count = Identity.objects.filter(environment__project=project).count()

        if identity_count > settings.MAX_SELF_MIGRATABLE_IDENTITIES:
            raise TooManyIdentitiesError()

        identity_migrator = IdentityMigrator(project.id)

        if not identity_migrator.can_migrate:
            raise ProjectMigrationError()

        identity_migrator.trigger_migration()
        return Response(status=status.HTTP_202_ACCEPTED)


class BaseProjectPermissionsViewSet(viewsets.ModelViewSet):
    model_class = None
    pagination_class = None
    permission_classes = [IsAuthenticated, IsProjectAdmin]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()

        if not self.kwargs.get("project_pk"):
            raise ValidationError("Missing project pk.")

        return self.model_class.objects.filter(project__pk=self.kwargs["project_pk"])

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs["project_pk"])

    def perform_update(self, serializer):
        serializer.save(project_id=self.kwargs["project_pk"])


class UserProjectPermissionsViewSet(BaseProjectPermissionsViewSet):
    model_class = UserProjectPermission

    def get_serializer_class(self):
        if self.action == "list":
            return ListUserProjectPermissionSerializer

        return CreateUpdateUserProjectPermissionSerializer


class UserPermissionGroupProjectPermissionsViewSet(BaseProjectPermissionsViewSet):
    model_class = UserPermissionGroupProjectPermission

    def get_serializer_class(self):
        if self.action == "list":
            return ListUserPermissionGroupProjectPermissionSerializer

        return CreateUpdateUserPermissionGroupProjectPermissionSerializer


@swagger_auto_schema(method="GET", responses={200: UserObjectPermissionsSerializer()})
@api_view(http_method_names=["GET"])
@permission_classes([IsAuthenticated, IsProjectAdmin])
def get_user_project_permissions(request, **kwargs):
    user_id = kwargs["user_pk"]

    permission_data = get_project_permission_data(kwargs["project_pk"], user_id=user_id)
    # TODO: expose `user` and `groups` attributes from user_permissions_data
    serializer = UserObjectPermissionsSerializer(instance=permission_data)
    return Response(serializer.data)

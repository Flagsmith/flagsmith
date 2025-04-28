# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from common.projects.permissions import (
    TAG_SUPPORTED_PERMISSIONS,
    VIEW_PROJECT,
)
from django.conf import settings
from django.utils.decorators import method_decorator
from drf_yasg import openapi  # type: ignore[import-untyped]
from drf_yasg.utils import no_body, swagger_auto_schema  # type: ignore[import-untyped]
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
    UserDetailedPermissionsSerializer,
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
from projects.permissions import IsProjectAdmin, ProjectPermissions
from projects.serializers import (
    CreateUpdateUserPermissionGroupProjectPermissionSerializer,
    CreateUpdateUserProjectPermissionSerializer,
    ListUserPermissionGroupProjectPermissionSerializer,
    ListUserProjectPermissionSerializer,
    ProjectCreateSerializer,
    ProjectListSerializer,
    ProjectRetrieveSerializer,
    ProjectUpdateSerializer,
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
class ProjectViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    permission_classes = [ProjectPermissions]

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        serializers = {
            "retrieve": ProjectRetrieveSerializer,
            "create": ProjectCreateSerializer,
            "update": ProjectUpdateSerializer,
            "partial_update": ProjectUpdateSerializer,
        }
        return serializers.get(self.action, ProjectListSerializer)

    pagination_class = None

    def get_serializer_context(self):  # type: ignore[no-untyped-def]
        return super().get_serializer_context()

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return Project.objects.none()

        queryset = self.request.user.get_permitted_projects(permission_key=VIEW_PROJECT)  # type: ignore[union-attr]

        organisation_id = self.request.query_params.get("organisation")
        if organisation_id:
            queryset = queryset.filter(organisation__id=organisation_id)

        project_uuid = self.request.query_params.get("uuid")
        if project_uuid:
            queryset = queryset.filter(uuid=project_uuid)

        return queryset

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        project = serializer.save()
        if getattr(self.request.user, "is_master_api_key_user", False) is False:
            UserProjectPermission.objects.create(  # type: ignore[misc]
                user=self.request.user, project=project, admin=True
            )

    @action(
        detail=False,
        url_path=r"get-by-uuid/(?P<uuid>[0-9a-f-]+)",
        methods=["get"],
    )
    def get_by_uuid(self, request, uuid):  # type: ignore[no-untyped-def]
        qs = self.get_queryset()  # type: ignore[no-untyped-call]
        project = get_object_or_404(qs, uuid=uuid)
        serializer = self.get_serializer(project)
        return Response(serializer.data)

    @action(detail=True)
    def environments(self, request, pk):  # type: ignore[no-untyped-def]
        project = self.get_object()
        environments = project.environments.all()
        return Response(EnvironmentSerializerLight(environments, many=True).data)

    @swagger_auto_schema(
        responses={200: PermissionModelSerializer(many=True)}, request_body=no_body
    )
    @action(detail=False, methods=["GET"])
    def permissions(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return Response(
            PermissionModelSerializer(
                instance=ProjectPermissionModel.objects.all(),
                many=True,
                context={"tag_supported_permissions": TAG_SUPPORTED_PERMISSIONS},
            ).data
        )

    @swagger_auto_schema(
        responses={200: UserDetailedPermissionsSerializer},
    )
    @action(
        detail=True,
        methods=["GET"],
        url_path=r"user-detailed-permissions/(?P<user_id>\d+)",
        url_name="user-detailed-permissions",
    )
    def detailed_permissions(
        self, request: Request, pk: int = None, user_id: int = None
    ) -> Response:
        user_id = int(user_id)
        # TODO: permission checks
        project = self.get_object()
        permission_data = get_project_permission_data(project.id, user_id)
        serializer = UserDetailedPermissionsSerializer(
            permission_data.to_detailed_permissions_data()
        )
        return Response(serializer.data)

    @swagger_auto_schema(responses={200: UserObjectPermissionsSerializer()})  # type: ignore[misc]
    @action(
        detail=True,
        methods=["GET"],
        url_path="my-permissions",
        url_name="my-permissions",
    )
    def user_permissions(self, request: Request, pk: int = None):  # type: ignore[no-untyped-def,assignment]
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

    @swagger_auto_schema(  # type: ignore[misc]
        responses={202: "Migration event generated"}, request_body=no_body
    )
    @action(
        detail=True,
        methods=["POST"],
        url_path="migrate-to-edge",
    )
    def migrate_to_edge(self, request: Request, pk: int = None):  # type: ignore[no-untyped-def,assignment]
        if not settings.PROJECT_METADATA_TABLE_NAME_DYNAMO:
            raise DynamoNotEnabledError()

        project = self.get_object()
        if project.is_too_large:
            raise ProjectTooLargeError()

        identity_count = Identity.objects.filter(environment__project=project).count()

        if identity_count > settings.MAX_SELF_MIGRATABLE_IDENTITIES:
            raise TooManyIdentitiesError()

        identity_migrator = IdentityMigrator(project.id)  # type: ignore[no-untyped-call]

        if not identity_migrator.can_migrate:
            raise ProjectMigrationError()

        identity_migrator.trigger_migration()  # type: ignore[no-untyped-call]
        return Response(status=status.HTTP_202_ACCEPTED)


class BaseProjectPermissionsViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    model_class = None
    pagination_class = None
    permission_classes = [IsAuthenticated, IsProjectAdmin]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return self.model_class.objects.none()  # type: ignore[attr-defined]

        if not self.kwargs.get("project_pk"):
            raise ValidationError("Missing project pk.")

        return self.model_class.objects.filter(project__pk=self.kwargs["project_pk"])  # type: ignore[attr-defined]

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        serializer.save(project_id=self.kwargs["project_pk"])

    def perform_update(self, serializer):  # type: ignore[no-untyped-def]
        serializer.save(project_id=self.kwargs["project_pk"])


class UserProjectPermissionsViewSet(BaseProjectPermissionsViewSet):
    model_class = UserProjectPermission  # type: ignore[assignment]

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if self.action == "list":
            return ListUserProjectPermissionSerializer

        return CreateUpdateUserProjectPermissionSerializer


class UserPermissionGroupProjectPermissionsViewSet(BaseProjectPermissionsViewSet):
    model_class = UserPermissionGroupProjectPermission  # type: ignore[assignment]

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if self.action == "list":
            return ListUserPermissionGroupProjectPermissionSerializer

        return CreateUpdateUserPermissionGroupProjectPermissionSerializer


@swagger_auto_schema(method="GET", responses={200: UserObjectPermissionsSerializer()})
@api_view(http_method_names=["GET"])  # type: ignore[arg-type]
@permission_classes([IsAuthenticated, IsProjectAdmin])
def get_user_project_permissions(request, **kwargs):  # type: ignore[no-untyped-def]
    user_id = kwargs["user_pk"]

    permission_data = get_project_permission_data(kwargs["project_pk"], user_id=user_id)
    # TODO: expose `user` and `groups` attributes from user_permissions_data
    serializer = UserObjectPermissionsSerializer(instance=permission_data)
    return Response(serializer.data)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.decorators import method_decorator
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from environments.serializers import EnvironmentSerializerLight
from permissions.serializers import (
    PermissionModelSerializer,
    UserObjectPermissionsSerializer,
)
from projects.models import (
    Project,
    ProjectPermissionModel,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from projects.permissions import (
    IsProjectAdmin,
    NestedProjectPermissions,
    ProjectPermissions,
)
from projects.permissions_calculator import ProjectPermissionsCalculator
from projects.serializers import (
    CreateUpdateUserPermissionGroupProjectPermissionSerializer,
    CreateUpdateUserProjectPermissionSerializer,
    ListUserPermissionGroupProjectPermissionSerializer,
    ListUserProjectPermissionSerializer,
    ProjectSerializer,
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
            )
        ]
    ),
)
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, ProjectPermissions]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        queryset = user.get_permitted_projects(permissions=["VIEW_PROJECT"])

        organisation_id = self.request.query_params.get("organisation")
        if organisation_id:
            queryset = queryset.filter(organisation__id=organisation_id)

        return queryset

    def perform_create(self, serializer):
        project = serializer.save()
        UserProjectPermission.objects.create(
            user=self.request.user, project=project, admin=True
        )

    @action(detail=True)
    def environments(self, request, pk):
        project = self.get_object()
        environments = project.environments.all()
        return Response(EnvironmentSerializerLight(environments, many=True).data)

    @swagger_auto_schema(responses={200: PermissionModelSerializer})
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
        project_permissions_calculator = ProjectPermissionsCalculator(project_id=pk)
        permission_data = (
            project_permissions_calculator.get_user_project_permission_data(
                user_id=request.user.id
            )
        )
        serializer = UserObjectPermissionsSerializer(instance=permission_data)
        return Response(serializer.data)


class UserProjectPermissionsViewSet(viewsets.ModelViewSet):
    pagination_class = None
    permission_classes = [IsAuthenticated, NestedProjectPermissions]

    def get_queryset(self):
        if not self.kwargs.get("project_pk"):
            raise ValidationError("Missing project pk.")

        return UserProjectPermission.objects.filter(
            project__pk=self.kwargs["project_pk"]
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ListUserProjectPermissionSerializer

        return CreateUpdateUserProjectPermissionSerializer

    def perform_create(self, serializer):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        serializer.save(project=project)

    def perform_update(self, serializer):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        serializer.save(project=project)


class UserPermissionGroupProjectPermissionsViewSet(viewsets.ModelViewSet):
    pagination_class = None
    permission_classes = [IsAuthenticated, NestedProjectPermissions]

    def get_queryset(self):
        if not self.kwargs.get("project_pk"):
            raise ValidationError("Missing project pk.")

        return UserPermissionGroupProjectPermission.objects.filter(
            project__pk=self.kwargs["project_pk"]
        )

    def get_serializer_class(self):
        if self.action == "list":
            return ListUserPermissionGroupProjectPermissionSerializer

        return CreateUpdateUserPermissionGroupProjectPermissionSerializer

    def perform_create(self, serializer):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        serializer.save(project=project)

    def perform_update(self, serializer):
        project = Project.objects.get(id=self.kwargs["project_pk"])
        serializer.save(project=project)


@swagger_auto_schema(method="GET", responses={200: UserObjectPermissionsSerializer()})
@api_view(http_method_names=["GET"])
@permission_classes([IsAuthenticated, IsProjectAdmin])
def get_user_project_permissions(request, **kwargs):
    user_id = kwargs["user_pk"]

    project_permissions_calculator = ProjectPermissionsCalculator(kwargs["project_pk"])
    user_permissions_data = (
        project_permissions_calculator.get_user_project_permission_data(user_id)
    )

    # TODO: expose `user` and `groups` attributes from user_permissions_data
    return Response(
        {
            "admin": user_permissions_data.admin,
            "permissions": user_permissions_data.permissions,
        }
    )

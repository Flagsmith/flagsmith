# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.utils.decorators import method_decorator
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from environments.permissions.permissions import (
    EnvironmentPermissions,
    NestedEnvironmentPermissions,
)
from permissions.serializers import (
    MyUserObjectPermissionsSerializer,
    PermissionModelSerializer,
)

from .identities.traits.models import Trait
from .identities.traits.serializers import (
    DeleteAllTraitKeysSerializer,
    TraitKeysSerializer,
)
from .models import Environment, Webhook
from .permissions.models import (
    EnvironmentPermissionModel,
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from .serializers import (
    CloneEnvironmentSerializer,
    EnvironmentSerializerLight,
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
class EnvironmentViewSet(viewsets.ModelViewSet):
    lookup_field = "api_key"
    permission_classes = [IsAuthenticated, EnvironmentPermissions]

    def get_serializer_class(self):
        if self.action == "trait_keys":
            return TraitKeysSerializer
        if self.action == "delete_traits":
            return DeleteAllTraitKeysSerializer
        if self.action == "clone":
            return CloneEnvironmentSerializer
        return EnvironmentSerializerLight

    def get_serializer_context(self):
        context = super(EnvironmentViewSet, self).get_serializer_context()
        if self.kwargs.get("api_key"):
            context["environment"] = self.get_object()
        return context

    def get_queryset(self):
        queryset = self.request.user.get_permitted_environments(["VIEW_ENVIRONMENT"])

        project_id = self.request.query_params.get("project")
        if project_id:
            queryset = queryset.filter(project__id=project_id)

        return queryset

    def perform_create(self, serializer):
        environment = serializer.save()
        UserEnvironmentPermission.objects.create(
            user=self.request.user, environment=environment, admin=True
        )

    @action(detail=True, methods=["GET"], url_path="trait-keys")
    def trait_keys(self, request, *args, **kwargs):
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
    def clone(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        clone = serializer.save(source_env=self.get_object())
        UserEnvironmentPermission.objects.create(
            user=self.request.user, environment=clone, admin=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"], url_path="delete-traits")
    def delete_traits(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.delete()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Couldn't delete trait keys."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @swagger_auto_schema(responses={200: PermissionModelSerializer})
    @action(detail=False, methods=["GET"])
    def permissions(self, *args, **kwargs):
        return Response(
            PermissionModelSerializer(
                instance=EnvironmentPermissionModel.objects.all(), many=True
            ).data
        )

    @swagger_auto_schema(responses={200: MyUserObjectPermissionsSerializer})
    @action(
        detail=True,
        methods=["GET"],
        url_path="my-permissions",
        url_name="my-permissions",
    )
    def user_permissions(self, request, *args, **kwargs):
        # TODO: tidy this mess up
        environment = self.get_object()

        group_permissions = UserPermissionGroupEnvironmentPermission.objects.filter(
            group__users=request.user, environment=environment
        )
        user_permissions = UserEnvironmentPermission.objects.filter(
            user=request.user, environment=environment
        )

        permissions = set()
        for group_permission in group_permissions:
            permissions = permissions.union(
                {
                    permission.key
                    for permission in group_permission.permissions.all()
                    if permission.key
                }
            )
        for user_permission in user_permissions:
            permissions = permissions.union(
                {
                    permission.key
                    for permission in user_permission.permissions.all()
                    if permission.key
                }
            )

        is_project_admin = request.user.is_project_admin(environment.project)

        data = {
            "admin": group_permissions.filter(admin=True).exists()
            or user_permissions.filter(admin=True).exists()
            or is_project_admin,
            "permissions": permissions,
        }

        serializer = MyUserObjectPermissionsSerializer(data=data)
        serializer.is_valid()

        return Response(serializer.data)


class WebhookViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = WebhookSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, NestedEnvironmentPermissions]

    def get_queryset(self):
        return Webhook.objects.filter(
            environment__api_key=self.kwargs.get("environment_api_key")
        )

    def perform_create(self, serializer):
        environment = Environment.objects.get(
            api_key=self.kwargs.get("environment_api_key")
        )
        serializer.save(environment=environment)

    def perform_update(self, serializer):
        environment = Environment.objects.get(
            api_key=self.kwargs.get("environment_api_key")
        )
        serializer.save(environment=environment)

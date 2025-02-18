from __future__ import unicode_literals

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from organisations.permissions.models import (
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from organisations.permissions.permissions import (
    NestedOrganisationEntityPermission,
)
from organisations.permissions.serializers import (
    UserOrganisationPermissionListSerializer,
    UserOrganisationPermissionUpdateCreateSerializer,
    UserPermissionGroupOrganisationPermissionListSerializer,
    UserPermissionGroupOrganisationPermissionUpdateCreateSerializer,
)


class BaseOrganisationPermissionViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,  # type: ignore[type-arg]
):
    pagination_class = None
    permission_classes = [IsAuthenticated, NestedOrganisationEntityPermission]

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        serializer.save(organisation_id=self.kwargs.get("organisation_pk"))


class UserOrganisationPermissionViewSet(BaseOrganisationPermissionViewSet):
    filterset_fields = ["user"]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        return UserOrganisationPermission.objects.select_related("user").filter(  # type: ignore[misc]
            organisation_id=self.kwargs.get("organisation_pk")
        )

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        return {"list": UserOrganisationPermissionListSerializer}.get(
            self.action, UserOrganisationPermissionUpdateCreateSerializer
        )


class UserPermissionGroupOrganisationPermissionViewSet(
    BaseOrganisationPermissionViewSet
):
    filterset_fields = ["group"]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        return UserPermissionGroupOrganisationPermission.objects.select_related(  # type: ignore[misc]
            "group"
        ).filter(
            organisation_id=self.kwargs.get("organisation_pk")
        )

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        return {"list": UserPermissionGroupOrganisationPermissionListSerializer}.get(
            self.action, UserPermissionGroupOrganisationPermissionUpdateCreateSerializer
        )

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from organisations.permissions.permissions import (
    NestedIsOrganisationAdminPermission,
)
from organisations.roles.models import Role

from .serializers import RoleSerializer


class RoleViewSet(viewsets.ModelViewSet):
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, NestedIsOrganisationAdminPermission]

    def get_queryset(self):
        if "organisation_pk" not in self.kwargs:
            raise ValidationError("Missing required path parameter 'organisation_pk'")

        return Role.objects.filter(organisation_id=self.kwargs["organisation_pk"])

    def perform_update(self, serializer):
        organisation_id = self.kwargs["organisation_pk"]
        serializer.save(organisation_id=organisation_id)

    def perform_create(self, serializer):
        organisation_id = self.kwargs["organisation_pk"]
        serializer.save(organisation_id=organisation_id)

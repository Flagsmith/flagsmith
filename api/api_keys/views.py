from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from organisations.permissions.permissions import (
    NestedIsOrganisationAdminPermission,
)

from .models import MasterAPIKey
from .serializers import MasterAPIKeySerializer


class MasterAPIKeyViewSet(viewsets.ModelViewSet):
    lookup_field = "prefix"
    serializer_class = MasterAPIKeySerializer

    permission_classes = [IsAuthenticated, NestedIsOrganisationAdminPermission]

    def get_queryset(self):
        return MasterAPIKey.objects.filter(
            organisation_id=self.kwargs.get("organisation_pk")
        )

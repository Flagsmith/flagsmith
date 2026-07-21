from rest_framework import viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import IsAuthenticated

from organisations.permissions.permissions import (
    NestedIsOrganisationAdminPermission,
)

from .authentication import MasterAPIKeyAuthentication
from .models import MasterAPIKey
from .serializers import MasterAPIKeySerializer


class MasterAPIKeyViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    lookup_field = "prefix"
    serializer_class = MasterAPIKeySerializer

    permission_classes = [IsAuthenticated, NestedIsOrganisationAdminPermission]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        return MasterAPIKey.objects.filter(
            organisation_id=self.kwargs.get("organisation_pk"), revoked=False
        )

    def get_authenticators(self) -> list[BaseAuthentication]:
        # API Keys should not be able to create API Keys
        return [
            authenticator
            for authenticator in super().get_authenticators()
            if not isinstance(authenticator, MasterAPIKeyAuthentication)
        ]

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        serializer.save(
            organisation_id=self.kwargs.get("organisation_pk"),
            created_by=self.request.user,
        )

from rest_framework import viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from organisations.permissions.permissions import (
    NestedIsOrganisationAdminPermission,
)

from .authentication import MasterAPIKeyAuthentication
from .models import MasterAPIKey
from .serializers import MasterAPIKeySerializer


class ExcludeMasterAPIKeyAuthenticationMixin(APIView):
    # Machine credentials must not be able to manage machine credentials.
    def get_authenticators(self) -> list[BaseAuthentication]:
        return [
            authenticator
            for authenticator in super().get_authenticators()
            if not isinstance(authenticator, MasterAPIKeyAuthentication)
        ]


class MasterAPIKeyViewSet(
    ExcludeMasterAPIKeyAuthenticationMixin,
    viewsets.ModelViewSet,  # type: ignore[type-arg]
):
    lookup_field = "prefix"
    serializer_class = MasterAPIKeySerializer

    permission_classes = [IsAuthenticated, NestedIsOrganisationAdminPermission]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        return MasterAPIKey.objects.filter(
            organisation_id=self.kwargs.get("organisation_pk"),
            revoked=False,
            trust_relationship__isnull=True,
        )

    def perform_create(self, serializer):  # type: ignore[no-untyped-def]
        serializer.save(
            organisation_id=self.kwargs.get("organisation_pk"),
            created_by=self.request.user,
        )

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from api_keys.authentication import MasterAPIKeyAuthentication
from organisations.permissions.permissions import (
    NestedIsOrganisationAdminPermission,
)
from trust_relationships.models import TrustRelationship
from trust_relationships.serializers import TrustRelationshipSerializer
from trust_relationships.services import delete_trust_relationship


class TrustRelationshipViewSet(viewsets.ModelViewSet[TrustRelationship]):
    serializer_class = TrustRelationshipSerializer

    permission_classes = [IsAuthenticated, NestedIsOrganisationAdminPermission]

    def get_queryset(self) -> QuerySet[TrustRelationship]:
        queryset: QuerySet[TrustRelationship] = TrustRelationship.objects.filter(
            organisation_id=self.kwargs["organisation_pk"]
        ).select_related("master_api_key")
        return queryset

    def get_authenticators(self) -> list[BaseAuthentication]:
        # Machine credentials must not be able to manage trust relationships.
        return [
            authenticator
            for authenticator in super().get_authenticators()
            if not isinstance(authenticator, MasterAPIKeyAuthentication)
        ]

    def perform_create(self, serializer: BaseSerializer[TrustRelationship]) -> None:
        serializer.save(
            organisation_id=int(self.kwargs["organisation_pk"]),
            created_by=self.request.user,
        )

    def perform_destroy(self, instance: TrustRelationship) -> None:
        delete_trust_relationship(trust_relationship=instance)

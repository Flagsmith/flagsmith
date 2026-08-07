from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer

from api_keys.views import ExcludeMasterAPIKeyAuthenticationMixin
from organisations.permissions.permissions import (
    NestedIsOrganisationAdminPermission,
)
from trust_relationships.models import TrustRelationship
from trust_relationships.serializers import TrustRelationshipSerializer
from trust_relationships.services import delete_trust_relationship


class TrustRelationshipViewSet(
    ExcludeMasterAPIKeyAuthenticationMixin,
    viewsets.ModelViewSet[TrustRelationship],
):
    serializer_class = TrustRelationshipSerializer

    permission_classes = [IsAuthenticated, NestedIsOrganisationAdminPermission]

    def get_queryset(self) -> QuerySet[TrustRelationship]:
        if getattr(self, "swagger_fake_view", False):
            empty: QuerySet[TrustRelationship] = TrustRelationship.objects.none()
            return empty
        queryset: QuerySet[TrustRelationship] = TrustRelationship.objects.filter(
            organisation_id=self.kwargs["organisation_pk"]
        ).select_related("master_api_key")
        return queryset

    def perform_create(self, serializer: BaseSerializer[TrustRelationship]) -> None:
        serializer.save(
            organisation_id=int(self.kwargs["organisation_pk"]),
            created_by=self.request.user,
        )

    def perform_destroy(self, instance: TrustRelationship) -> None:
        delete_trust_relationship(trust_relationship=instance)

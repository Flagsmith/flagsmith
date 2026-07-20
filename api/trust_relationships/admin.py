from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from trust_relationships.models import TrustRelationship
from trust_relationships.services import delete_trust_relationship


@admin.register(TrustRelationship)
class TrustRelationshipAdmin(admin.ModelAdmin[TrustRelationship]):
    list_display = ("name", "organisation", "issuer", "audience", "created_at")
    list_filter = ("issuer",)
    search_fields = ("name", "issuer", "audience")

    # Deletes must go through the service layer so the backing key is revoked.
    def delete_model(self, request: HttpRequest, obj: TrustRelationship) -> None:
        delete_trust_relationship(trust_relationship=obj)

    def delete_queryset(
        self, request: HttpRequest, queryset: QuerySet[TrustRelationship]
    ) -> None:
        for obj in queryset:
            delete_trust_relationship(trust_relationship=obj)

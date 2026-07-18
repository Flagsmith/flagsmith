from django.contrib import admin

from trust_relationships.models import TrustRelationship


@admin.register(TrustRelationship)
class TrustRelationshipAdmin(admin.ModelAdmin[TrustRelationship]):
    list_display = ("name", "organisation", "issuer", "audience", "created_at")
    list_filter = ("issuer",)
    search_fields = ("name", "issuer", "audience")

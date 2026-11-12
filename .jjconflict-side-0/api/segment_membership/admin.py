from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from segment_membership.models import SegmentMembershipSeed


@admin.register(SegmentMembershipSeed)
class SegmentMembershipSeedAdmin(admin.ModelAdmin[SegmentMembershipSeed]):
    actions = ["force_reseed"]
    list_display = ("organisation", "seeded_at")
    readonly_fields = ("seeded_at",)
    autocomplete_fields = ("organisation",)

    @admin.action(description="Force re-seed (clears the marker)")
    def force_reseed(
        self,
        request: HttpRequest,
        queryset: QuerySet[SegmentMembershipSeed],
    ) -> None:
        from segment_membership.tasks import seed_organisation_identities

        queryset.update(seeded_at=None)
        for seed in queryset:
            seed_organisation_identities.delay(args=(seed.organisation_id,))

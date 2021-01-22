from django.contrib import admin

from organisations.invites.models import Invite


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    date_hierarchy = "date_created"
    list_display = (
        "email",
        "invited_by",
        "organisation",
        "date_created",
    )
    list_filter = (
        "date_created",
        "organisation",
    )
    list_select_related = (
        "organisation",
        "invited_by",
    )
    raw_id_fields = ("invited_by",)
    search_fields = (
        "email",
        "invited_by__email",
        "invited_by__username",
        "invited_by__first_name",
        "invited_by__last_name",
        "organisation__name",
    )

from django.contrib import admin

from custom_auth.mfa.trench.models import MFAMethod


@admin.register(MFAMethod)
class MFAMethodAdmin(admin.ModelAdmin):  # pragma: no cover
    list_display = (
        "user_email",
        "name",
        "is_active",
        "is_primary",
        "created_at",
        "updated_at",
    )
    search_fields = ("user__email", "name")
    list_filter = ("is_active", "is_primary")

    list_select_related = ("user",)

    fields = (
        "user",
        "name",
        "created_at",
        "updated_at",
        "is_active",
        "is_primary",
    )

    readonly_fields = (
        "user",
        "name",
        "created_at",
        "updated_at",
        "is_primary",
    )

    def user_email(self, instance: MFAMethod) -> str:
        return instance.user.email

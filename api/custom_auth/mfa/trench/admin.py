from django.contrib import admin

from custom_auth.mfa.trench.models import MFAMethod


@admin.register(MFAMethod)
class MFAMethodAdmin(admin.ModelAdmin):
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

    def user_email(self, instance: MFAMethod) -> str:
        return instance.user.email

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from organisations.models import UserOrganisation

from .forms import CustomUserAdminForm
from .models import FFAdminUser


class UserOrganisationInline(admin.TabularInline):
    model = UserOrganisation
    extra = 0
    show_change_link = False
    autocomplete_fields = ("organisation",)
    verbose_name_plural = "Organisations"


@admin.register(FFAdminUser)
class CustomUserAdmin(UserAdmin):
    model = FFAdminUser
    form = CustomUserAdminForm

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    date_hierarchy = "date_joined"

    list_display = (
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "date_joined",
    )

    list_filter = (
        "is_staff",
        "is_active",
        "date_joined",
        "organisations",
    )

    search_fields = (
        "email",
        "username",
        "first_name",
        "last_name",
    )

    inlines = [UserOrganisationInline]

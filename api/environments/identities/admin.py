from django.conf import settings
from django.contrib import admin

from .models import Identity


class IdentityAdmin(admin.ModelAdmin):
    date_hierarchy = "created_date"
    list_display = ("__str__", "created_date", "environment")
    list_filter = ("created_date", "environment")
    search_fields = ("identifier",)


if settings.ENV in ("local", "dev"):
    # identities be displayed in prod envs but are useful in development envs
    admin.site.register(Identity, IdentityAdmin)

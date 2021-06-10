from django.conf import settings
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Trait


class TraitAdmin(SimpleHistoryAdmin):
    date_hierarchy = "created_date"
    list_display = (
        "__str__",
        "value_type",
        "boolean_value",
        "integer_value",
        "string_value",
        "float_value",
        "created_date",
        "identity",
    )
    list_filter = (
        "value_type",
        "created_date",
        "identity",
    )
    raw_id_fields = ("identity",)
    search_fields = (
        "string_value",
        "trait_key",
        "identity__identifier",
    )


if settings.ENV in ("local", "dev"):
    # traits shouldn't be displayed in prod envs but are useful in development envs
    admin.site.register(Trait, TraitAdmin)

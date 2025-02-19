from django.contrib import admin

from projects.tags.models import Tag


# Register your models here.
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("label", "color", "project")
    list_select_related = ("project",)
    search_fields = (
        "label",
        "project__name",
    )

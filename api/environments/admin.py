# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Environment, Webhook
from .tasks import rebuild_environment_document


class WebhookInline(admin.TabularInline):
    model = Webhook
    extra = 0


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    actions = ["rebuild_environments"]
    date_hierarchy = "created_date"
    list_display = (
        "name",
        "__str__",
        "created_date",
    )
    list_filter = (
        "created_date",
        "project",
    )
    search_fields = (
        "name",
        "project__name",
        "api_key",
    )
    inlines = (WebhookInline,)

    @admin.action(description="Rebuild selected environment documents")
    def rebuild_environments(self, request, queryset):
        for environment in queryset:
            rebuild_environment_document.delay(args=(environment.id,))

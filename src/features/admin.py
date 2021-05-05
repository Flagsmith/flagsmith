# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Feature, FeatureSegment, FeatureState, FeatureStateValue


class FeatureStateValueInline(admin.StackedInline):
    model = FeatureStateValue
    extra = 0
    show_change_link = True


class FeatureAdmin(SimpleHistoryAdmin):
    date_hierarchy = "created_date"
    list_display = (
        "__str__",
        "initial_value",
        "default_enabled",
        "type",
        "created_date",
    )
    list_filter = (
        "type",
        "default_enabled",
        "created_date",
        "project",
    )
    list_select_related = ("project",)
    search_fields = (
        "project__name",
        "name",
        "initial_value",
        "description",
        "tags__label",
    )
    readonly_fields = ("project",)


class FeatureSegmentAdmin(admin.ModelAdmin):
    model = FeatureSegment

    def add_view(self, *args, **kwargs):
        self.exclude = ("priority",)
        return super(FeatureSegmentAdmin, self).add_view(*args, **kwargs)

    def change_view(self, *args, **kwargs):
        self.exclude = ()
        return super(FeatureSegmentAdmin, self).change_view(*args, **kwargs)


class FeatureStateAdmin(SimpleHistoryAdmin):
    inlines = [
        FeatureStateValueInline,
    ]
    list_display = (
        "__str__",
        "enabled",
    )
    list_filter = (
        "enabled",
        "environment",
        "feature",
    )
    list_select_related = (
        "environment",
        "feature",
        "identity",
    )
    raw_id_fields = ("identity",)
    search_fields = (
        "feature__name",
        "feature__project__name",
        "environment__name",
        "identity__identifier",
    )


class FeatureStateValueAdmin(SimpleHistoryAdmin):
    list_display = (
        "feature_state",
        "type",
        "boolean_value",
        "integer_value",
        "string_value",
    )
    list_filter = (
        "type",
        "boolean_value",
    )
    list_select_related = ("feature_state",)
    raw_id_fields = ("feature_state",)
    search_fields = (
        "string_value",
        "feature_state__feature__name",
        "feature_state__feature__project__name",
        "feature_state__environment__name",
        "feature_state__identity__identifier",
    )


if settings.ENV in ("local", "dev"):
    admin.site.register(Feature, FeatureAdmin)
    admin.site.register(FeatureState, FeatureStateAdmin)
    admin.site.register(FeatureSegment, FeatureSegmentAdmin)
    admin.site.register(FeatureStateValue, FeatureStateValueAdmin)

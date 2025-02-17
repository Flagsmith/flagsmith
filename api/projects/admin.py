# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from environments.models import Environment
from features.models import Feature
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Segment


class EnvironmentInline(admin.StackedInline):  # type: ignore[type-arg]
    model = Environment
    extra = 0
    show_change_link = True
    fields = ("name", "api_key", "minimum_change_request_approvals")


class FeatureInline(admin.StackedInline):  # type: ignore[type-arg]
    model = Feature
    extra = 0
    show_change_link = True
    fields = (
        "name",
        "description",
        "initial_value",
        "default_enabled",
        "type",
        "is_archived",
    )


class SegmentInline(admin.StackedInline):  # type: ignore[type-arg]
    model = Segment
    extra = 0
    show_change_link = True
    fields = ("name", "description")


class TagInline(admin.StackedInline):  # type: ignore[type-arg]
    model = Tag
    extra = 0
    show_change_link = True
    fields = ("label", "description", "color")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    actions = ["delete_all_segments"]
    date_hierarchy = "created_date"
    inlines = [EnvironmentInline, FeatureInline, SegmentInline, TagInline]
    list_display = (
        "name",
        "organisation",
        "created_date",
    )
    list_filter = ("created_date", "enable_dynamo_db")
    list_select_related = ("organisation",)
    search_fields = ("name", "organisation__name")
    fields = (
        "name",
        "organisation",
        "hide_disabled_flags",
        "enable_dynamo_db",
        "enable_realtime_updates",
        "max_segments_allowed",
        "max_features_allowed",
        "max_segment_overrides_allowed",
        "edge_v2_migration_status",
        "edge_v2_migration_read_capacity_budget",
    )

    @admin.action(
        description="Delete all segments for project",
        permissions=["delete_all_segments"],
    )
    def delete_all_segments(self, request: HttpRequest, queryset: QuerySet):  # type: ignore[no-untyped-def,type-arg]
        Segment.objects.filter(project__in=queryset).delete()

    def has_delete_all_segments_permission(
        self, request: HttpRequest, obj: Project = None  # type: ignore[assignment]
    ) -> bool:
        return request.user.is_superuser

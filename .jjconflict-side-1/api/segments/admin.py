from django.conf import settings
from django.contrib import admin

from segments.models import Condition, Segment, SegmentRule


class RulesInline(admin.StackedInline):  # type: ignore[type-arg]
    model = SegmentRule
    extra = 0
    show_change_link = True


class ConditionsInline(admin.StackedInline):  # type: ignore[type-arg]
    model = Condition
    extra = 0
    show_change_link = True


class SegmentAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    inlines = [RulesInline]


class SegmentRuleAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    inlines = [ConditionsInline]


if settings.ENV == ("local", "dev"):
    admin.site.register(Segment, SegmentAdmin)
    admin.site.register(SegmentRule, SegmentRuleAdmin)

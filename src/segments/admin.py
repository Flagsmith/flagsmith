from django.contrib import admin

from segments.models import SegmentRule, Condition, Segment


class RulesInline(admin.StackedInline):
    model = SegmentRule
    extra = 0
    show_change_link = True


class ConditionsInline(admin.StackedInline):
    model = Condition
    extra = 0
    show_change_link = True


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    inlines = [
        RulesInline
    ]


@admin.register(SegmentRule)
class SegmentRule(admin.ModelAdmin):
    inlines = [
        ConditionsInline
    ]

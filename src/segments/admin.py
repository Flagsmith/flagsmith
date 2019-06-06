from django.contrib import admin

from segments.models import SegmentRule, Condition, Segment


class ConditionsInline(admin.StackedInline):
    model = Condition
    extra = 0
    show_change_link = True


class ChildRulesInline(admin.StackedInline):
    model = SegmentRule
    extra = 0
    show_change_link = True


@admin.register(SegmentRule)
class RulesAdmin(admin.ModelAdmin):
    model = SegmentRule
    inlines = [ConditionsInline, ChildRulesInline]


class RulesInline(admin.StackedInline):
    model = SegmentRule
    extra = 0
    show_change_link = True


@admin.register(Segment)
class SegmentAdmin(admin.ModelAdmin):
    inlines = [RulesInline]

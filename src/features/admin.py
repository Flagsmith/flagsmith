# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Feature, FeatureState, FeatureStateValue


class FeatureStateValueInline(admin.StackedInline):
    model = FeatureStateValue
    extra = 0
    show_change_link = True


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_date'
    list_display = ('__str__', 'initial_value', 'default_enabled', 'type', 'created_date', )
    list_filter = ('type', 'default_enabled', 'created_date', 'project', )
    list_select_related = ('project', )
    search_fields = (
        'project__name',
        'name',
        'initial_value',
        'description',
    )


@admin.register(FeatureState)
class FeatureStateAdmin(admin.ModelAdmin):
    inlines = [
        FeatureStateValueInline,
    ]
    list_display = ('__str__', 'enabled', )
    list_filter = ('enabled', 'environment', 'feature', )
    list_select_related = ('environment', 'feature', 'identity', )
    raw_id_fields = ('identity', )
    search_fields = (
        'feature__name',
        'feature__project__name',
        'environment__name',
        'identity__identifier',
    )


@admin.register(FeatureStateValue)
class FeatureStateValueAdmin(admin.ModelAdmin):
    list_display = ('feature_state', 'type', 'boolean_value', 'integer_value', 'string_value', )
    list_filter = ('type', 'boolean_value', )
    list_select_related = ('feature_state',)
    raw_id_fields = ('feature_state', )
    search_fields = (
        'string_value',
        'feature_state__feature__name',
        'feature_state__feature__project__name',
        'feature_state__environment__name',
        'feature_state__identity__identifier',
    )

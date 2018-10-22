# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Identity, Environment, Trait, TraitValue


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_date'
    list_display = ('name', '__str__', 'created_date', )
    list_filter = ('created_date', 'project', )
    search_fields = ('name', 'project__name', 'api_key', )


@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_date'
    list_display = ('__str__', 'created_date', 'environment', )
    list_filter = ('created_date', 'environment', )
    search_fields = ('identifier', )


class TraitValueInline(admin.StackedInline):
    model = TraitValue
    extra = 0
    show_change_link = True


@admin.register(Trait)
class TraitAdmin(SimpleHistoryAdmin):
    inlines = [
        TraitValueInline,
    ]
    date_hierarchy = 'created_date'
    list_display = ('__str__', 'created_date', 'identity', )
    list_filter = ('created_date', 'identity', )
    raw_id_fields = ('identity', )
    search_fields = ('identity__identifier', 'trait_key', )


@admin.register(TraitValue)
class TraitValue(SimpleHistoryAdmin):
    list_display = ('trait', 'type', 'boolean_value',
                    'integer_value', 'string_value', )
    list_filter = ('type', 'boolean_value', )
    list_select_related = ('trait',)
    raw_id_fields = ('trait', )
    search_fields = (
        'string_value',
        'trait__identity__environment__name',
        'trait__identity__identifier',
    )
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Identity, Environment, Trait, AuditLog


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_date'
    list_display = ('name', '__str__', 'created_date',)
    list_filter = ('created_date', 'project',)
    search_fields = ('name', 'project__name', 'api_key',)


@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_date'
    list_display = ('__str__', 'created_date', 'environment',)
    list_filter = ('created_date', 'environment',)
    search_fields = ('identifier',)


@admin.register(Trait)
class TraitAdmin(SimpleHistoryAdmin):
    date_hierarchy = 'created_date'
    list_display = ('__str__', 'value_type', 'boolean_value', 'integer_value', 'string_value',
                    'created_date', 'identity',)
    list_filter = ('value_type', 'created_date', 'identity',)
    raw_id_fields = ('identity',)
    search_fields = ('string_value', 'trait_key', 'identity__identifier',)


@admin.register(AuditLog)
class AuditLogAdmin(SimpleHistoryAdmin):
    date_hierarchy = 'created_date'
    list_display = ('__str__', 'created_date', 'environment',)
    list_filter = ('created_date', 'environment',)
    search_fields = ('log',)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Identity, Environment


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

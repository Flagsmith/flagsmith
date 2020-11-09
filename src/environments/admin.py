# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import admin

from .identities.traits.admin import TraitAdmin
from .models import Environment, Webhook
from .identities.traits.models import Trait


class WebhookInline(admin.TabularInline):
    model = Webhook
    extra = 0


@admin.register(Environment)
class EnvironmentAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_date'
    list_display = ('name', '__str__', 'created_date',)
    list_filter = ('created_date', 'project',)
    search_fields = ('name', 'project__name', 'api_key',)
    inlines = (WebhookInline,)

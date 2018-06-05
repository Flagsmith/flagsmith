# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Feature, FeatureState, FeatureStateValue


class FeatureStateValueInline(admin.StackedInline):
    model = FeatureStateValue


class FeatureStateAdmin(admin.ModelAdmin):
    inlines = [
        FeatureStateValueInline,
    ]


admin.site.register(FeatureState, FeatureStateAdmin)
admin.site.register(Feature)
admin.site.register(FeatureStateValue)


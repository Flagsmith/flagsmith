# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from environments.models import Environment
from features.models import Feature
from projects.models import Project


class EnvironmentInline(admin.StackedInline):
    model = Environment


class FeatureInline(admin.StackedInline):
    model = Feature


class ProjectAdmin(admin.ModelAdmin):
    inlines = [
        EnvironmentInline,
        FeatureInline
    ]


admin.site.register(Project, ProjectAdmin)

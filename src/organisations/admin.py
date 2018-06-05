# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from projects.models import Project
from organisations.models import Organisation


class ProjectInline(admin.StackedInline):
    model = Project


class OrganisationAdmin(admin.ModelAdmin):
    inlines = [
        ProjectInline
    ]


admin.site.register(Organisation, OrganisationAdmin)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from projects.models import Project
from organisations.models import Organisation, Subscription


class ProjectInline(admin.StackedInline):
    model = Project
    extra = 0
    show_change_link = True


class SubscriptionInline(admin.StackedInline):
    model = Subscription
    extra = 0
    show_change_link = True
    verbose_name_plural = 'Subscription'


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    inlines = [ProjectInline, SubscriptionInline]
    list_display = ('__str__', )
    list_filter = ('projects', 'subscription__plan')
    search_fields = ('name', )

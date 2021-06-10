# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from organisations.models import Organisation, Subscription, UserOrganisation
from projects.models import Project


class ProjectInline(admin.StackedInline):
    model = Project
    extra = 0
    show_change_link = True


class SubscriptionInline(admin.StackedInline):
    model = Subscription
    extra = 0
    show_change_link = True
    verbose_name_plural = "Subscription"


class UserOrganisationInline(admin.TabularInline):
    model = UserOrganisation
    extra = 0
    show_change_link = True
    autocomplete_fields = ("user",)
    verbose_name_plural = "Users"


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    inlines = [
        ProjectInline,
        SubscriptionInline,
        UserOrganisationInline,
    ]
    list_display = ("__str__",)
    list_filter = ("projects", "subscription__plan")
    search_fields = ("id", "name", "subscription__subscription_id")

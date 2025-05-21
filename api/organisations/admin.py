# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.db import models
from django.db.models import Count, Q

from organisations.models import (
    Organisation,
    OrganisationSubscriptionInformationCache,
    Subscription,
    UserOrganisation,
)
from projects.models import Project


class ProjectInline(admin.StackedInline[Project]):
    model = Project
    extra = 0
    show_change_link = True

    classes = ("collapse",)


class SubscriptionInline(admin.StackedInline[Subscription]):
    model = Subscription
    extra = 0
    show_change_link = True
    verbose_name_plural = "Subscription"


class UserOrganisationInline(admin.TabularInline[UserOrganisation]):
    model = UserOrganisation
    extra = 0
    show_change_link = True
    autocomplete_fields = ("user",)
    verbose_name_plural = "Users"


class OrganisationSubscriptionInformationCacheInline(
    admin.StackedInline[OrganisationSubscriptionInformationCache]
):
    model = OrganisationSubscriptionInformationCache
    extra = 0
    show_change_link = False
    classes = ("collapse",)

    fieldsets = (
        (
            None,
            {
                "fields": [],
                "description": "This data is relevant in SaaS only. It should all be managed automatically via "
                "webhooks from Chargebee and recurring tasks but may need to be edited in certain "
                "situtations.",
            },
        ),
        (
            "Usage Information",
            {
                "classes": ["collapse"],
                "fields": ["api_calls_24h", "api_calls_7d", "api_calls_30d"],
            },
        ),
        (
            "Billing Information",
            {
                "classes": ["collapse"],
                "fields": [
                    "current_billing_term_starts_at",
                    "current_billing_term_ends_at",
                    "chargebee_email",
                ],
            },
        ),
        (
            "Allowances",
            {
                "description": "These fields shouldn't need to be edited, as it should be managed automatically, "
                "but sometimes things get out of sync - in which case, we can edit them here.",
                "fields": [
                    "allowed_seats",
                    "allowed_30d_api_calls",
                    "allowed_projects",
                    "audit_log_visibility_days",
                    "feature_history_visibility_days",
                ],
            },
        ),
    )

    readonly_fields = (
        "api_calls_24h",
        "api_calls_7d",
        "api_calls_30d",
        "current_billing_term_starts_at",
        "current_billing_term_ends_at",
        "chargebee_email",
    )


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin[Organisation]):
    inlines = [
        ProjectInline,
        SubscriptionInline,
        UserOrganisationInline,
        OrganisationSubscriptionInformationCacheInline,
    ]
    list_display = (
        "id",
        "name",
        "subscription_id",
        "subscription_plan",
        "num_users",
        "num_projects",
        "created_date",
    )
    list_display_links = ("name",)
    list_filter = ("subscription__plan",)
    search_fields = ("id", "name", "subscription__subscription_id", "users__email")

    def get_queryset(
        self, request
    ) -> models.QuerySet[Organisation]:  # pragma: no cover
        return (
            Organisation.objects.select_related("subscription")
            .annotate(
                num_users=Count(
                    "users", distinct=True, filter=Q(users__is_active=True)
                ),
                num_projects=Count(
                    "projects",
                    distinct=True,
                    filter=Q(projects__deleted_at__isnull=True),
                ),
            )
            .all()
        )

    def num_users(self, instance: Organisation) -> int:
        return instance.num_users  # type: ignore[no-any-return]

    def num_projects(self, instance: Organisation) -> int:
        return instance.num_projects  # type: ignore[no-any-return]

    def subscription_id(self, instance: Organisation) -> str:
        if instance.subscription and instance.subscription.subscription_id:
            return instance.subscription.subscription_id
        return ""

    def subscription_plan(self, instance: Organisation) -> str:
        if instance.subscription and instance.subscription.plan:
            return instance.subscription.plan
        return ""

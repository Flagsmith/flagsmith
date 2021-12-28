# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import enum

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django_lifecycle import AFTER_CREATE, AFTER_SAVE, LifecycleModel, hook

from organisations.chargebee import (
    get_customer_id_from_subscription_id,
    get_max_seats_for_plan,
    get_portal_url,
)
from users.utils.mailer_lite import MailerLite

mailer_lite = MailerLite()
from webhooks.models import AbstractBaseWebhookModel


class OrganisationRole(enum.Enum):
    ADMIN = "ADMIN"
    USER = "USER"


organisation_roles = ((tag.name, tag.value) for tag in OrganisationRole)


@python_2_unicode_compatible
class Organisation(models.Model):
    name = models.CharField(max_length=2000)
    has_requested_features = models.BooleanField(default=False)
    webhook_notification_email = models.EmailField(null=True, blank=True)
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)
    alerted_over_plan_limit = models.BooleanField(default=False)
    stop_serving_flags = models.BooleanField(
        default=False,
        help_text="Enable this to cease serving flags for this organisation.",
    )
    restrict_project_create_to_admin = models.BooleanField(default=False)
    persist_trait_data = models.BooleanField(
        default=settings.DEFAULT_ORG_STORE_TRAITS_VALUE,
        help_text="Disable this if you don't want Flagsmith "
        "to store trait data for this org's identities.",
    )
    block_access_to_admin = models.BooleanField(
        default=False,
        help_text="Enable this to block all the access to admin "
        "interface for the organisation",
    )
    feature_analytics = models.BooleanField(
        default=False, help_text="Record feature analytics in InfluxDB"
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return "Org %s (#%s)" % (self.name, self.id)

    # noinspection PyTypeChecker
    def get_unique_slug(self):
        return str(self.id) + "-" + self.name

    @property
    def num_seats(self):
        return self.users.count()

    def has_subscription(self):
        return (
            hasattr(self, "subscription")
            and self.subscription.subscription_id is not None
        )

    @property
    def is_paid(self):
        return self.has_subscription() and self.subscription.cancellation_date is None

    def over_plan_seats_limit(self):
        if self.has_subscription():
            return self.num_seats > self.subscription.max_seats

        return self.num_seats > Subscription.MAX_SEATS_IN_FREE_PLAN

    def reset_alert_status(self):
        self.alerted_over_plan_limit = False
        self.save()


class UserOrganisation(models.Model):
    user = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=50, choices=organisation_roles)

    class Meta:
        unique_together = (
            "user",
            "organisation",
        )


class Subscription(LifecycleModel, models.Model):
    MAX_SEATS_IN_FREE_PLAN = 1

    organisation = models.OneToOneField(
        Organisation, on_delete=models.CASCADE, related_name="subscription"
    )
    subscription_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_date = models.DateTimeField(blank=True, null=True)
    plan = models.CharField(max_length=20, null=True, blank=True)
    max_seats = models.IntegerField(default=1)
    cancellation_date = models.DateTimeField(blank=True, null=True)
    customer_id = models.CharField(max_length=100, blank=True, null=True)

    CHARGEBEE = "CHARGEBEE"
    XERO = "XERO"
    PAYMENT_METHODS = [
        (CHARGEBEE, "Chargebee"),
        (XERO, "Xero"),
    ]
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default=CHARGEBEE,
    )
    notes = models.CharField(max_length=500, blank=True, null=True)

    def update_plan(self, plan_id):
        self.cancellation_date = None
        self.plan = plan_id
        self.max_seats = get_max_seats_for_plan(plan_id)
        self.save()

    @hook(AFTER_CREATE)
    @hook(AFTER_SAVE, when="cancellation_date", has_changed=True)
    def update_mailer_lite_subscribers(self):
        mailer_lite.update_organisation_users(self.organisation.id)

    def cancel(self, cancellation_date=timezone.now()):
        self.cancellation_date = cancellation_date
        self.save()

    def get_portal_url(self, redirect_url):
        if not self.subscription_id:
            return None

        if not self.customer_id:
            self.customer_id = get_customer_id_from_subscription_id(
                self.subscription_id
            )
            self.save()
        return get_portal_url(self.customer_id, redirect_url)


class OrganisationWebhook(AbstractBaseWebhookModel):
    name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="webhooks"
    )

    class Meta:
        ordering = ("id",)  # explicit ordering to prevent pagination warnings

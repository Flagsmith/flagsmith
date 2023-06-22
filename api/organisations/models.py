# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from core.models import SoftDeleteExportableModel
from django.conf import settings
from django.core.cache import caches
from django.db import models
from django.utils import timezone
from django_lifecycle import (
    AFTER_CREATE,
    AFTER_SAVE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)

from organisations.chargebee import (
    get_customer_id_from_subscription_id,
    get_max_api_calls_for_plan,
    get_max_seats_for_plan,
    get_plan_meta_data,
    get_portal_url,
    get_subscription_metadata,
)
from organisations.chargebee.chargebee import add_single_seat
from organisations.chargebee.chargebee import (
    cancel_subscription as cancel_chargebee_subscription,
)
from organisations.subscriptions.constants import (
    CHARGEBEE,
    FREE_PLAN_ID,
    MAX_API_CALLS_IN_FREE_PLAN,
    MAX_PROJECTS_IN_FREE_PLAN,
    MAX_SEATS_IN_FREE_PLAN,
    SUBSCRIPTION_PAYMENT_METHODS,
    XERO,
)
from organisations.subscriptions.exceptions import (
    SubscriptionDoesNotSupportSeatUpgrade,
)
from organisations.subscriptions.metadata import BaseSubscriptionMetadata
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata
from users.utils.mailer_lite import MailerLite
from webhooks.models import AbstractBaseExportableWebhookModel

TRIAL_SUBSCRIPTION_ID = "trial"

environment_cache = caches[settings.ENVIRONMENT_CACHE_NAME]


class OrganisationRole(models.TextChoices):
    ADMIN = ("ADMIN", "Admin")
    USER = ("USER", "User")


class Organisation(LifecycleModelMixin, SoftDeleteExportableModel):
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

    def has_subscription(self) -> bool:
        return hasattr(self, "subscription") and bool(self.subscription.subscription_id)

    @property
    def is_paid(self):
        return self.has_subscription() and self.subscription.cancellation_date is None

    def over_plan_seats_limit(self):
        if self.has_subscription():
            susbcription_metadata = self.subscription.get_subscription_metadata()
            return self.num_seats > susbcription_metadata.seats

        return self.num_seats > MAX_SEATS_IN_FREE_PLAN

    def reset_alert_status(self):
        self.alerted_over_plan_limit = False
        self.save()

    def seats_at_limit_and_can_not_auto_autoupgrade(self):
        if self.has_subscription():
            subscription_metadata = self.subscription.get_subscription_metadata()
            return (
                len(settings.AUTO_SEAT_UPGRADE_PLANS) > 0
                and self.num_seats >= subscription_metadata.seats
                and not self.subscription.can_auto_upgrade_seats
            )
        return self.num_seats >= MAX_SEATS_IN_FREE_PLAN

    @hook(BEFORE_DELETE)
    def cancel_subscription(self):
        if self.has_subscription():
            self.subscription.cancel()

    @hook(AFTER_CREATE)
    def create_subscription(self):
        Subscription.objects.create(organisation=self)

    @hook(AFTER_SAVE)
    def clear_environment_caches(self):
        from environments.models import Environment

        environment_cache.delete_many(
            list(
                Environment.objects.filter(project__organisation=self).values_list(
                    "api_key", flat=True
                )
            )
        )


class UserOrganisation(models.Model):
    user = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=50, choices=OrganisationRole.choices)

    class Meta:
        unique_together = (
            "user",
            "organisation",
        )


class Subscription(LifecycleModelMixin, SoftDeleteExportableModel):
    organisation = models.OneToOneField(
        Organisation, on_delete=models.CASCADE, related_name="subscription"
    )
    subscription_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_date = models.DateTimeField(blank=True, null=True)
    plan = models.CharField(max_length=100, null=True, blank=True, default=FREE_PLAN_ID)
    max_seats = models.IntegerField(default=1)
    max_api_calls = models.BigIntegerField(default=MAX_API_CALLS_IN_FREE_PLAN)
    cancellation_date = models.DateTimeField(blank=True, null=True)
    customer_id = models.CharField(max_length=100, blank=True, null=True)

    payment_method = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_PAYMENT_METHODS,
        blank=True,
        null=True,
    )
    notes = models.CharField(max_length=500, blank=True, null=True)

    def update_plan(self, plan_id):
        plan_metadata = get_plan_meta_data(plan_id)
        self.cancellation_date = None
        self.plan = plan_id
        self.max_seats = get_max_seats_for_plan(plan_metadata)
        self.max_api_calls = get_max_api_calls_for_plan(plan_metadata)
        self.save()

    @property
    def can_auto_upgrade_seats(self) -> bool:
        return self.plan in settings.AUTO_SEAT_UPGRADE_PLANS

    @hook(AFTER_SAVE, when="cancellation_date", has_changed=True)
    @hook(AFTER_SAVE, when="subscription_id", has_changed=True)
    def update_mailer_lite_subscribers(self):
        if settings.MAILERLITE_API_KEY:
            mailer_lite = MailerLite()
            mailer_lite.update_organisation_users(self.organisation.id)

    def cancel(self, cancellation_date=timezone.now(), update_chargebee=True):
        self.cancellation_date = cancellation_date
        self.save()
        if self.payment_method == CHARGEBEE and update_chargebee:
            cancel_chargebee_subscription(self.subscription_id)

    def get_portal_url(self, redirect_url):
        if not self.subscription_id:
            return None

        if not self.customer_id:
            self.customer_id = get_customer_id_from_subscription_id(
                self.subscription_id
            )
            self.save()
        return get_portal_url(self.customer_id, redirect_url)

    def get_subscription_metadata(self) -> BaseSubscriptionMetadata:
        metadata = None

        if self.subscription_id == TRIAL_SUBSCRIPTION_ID:
            metadata = BaseSubscriptionMetadata(
                seats=self.max_seats, api_calls=self.max_api_calls
            )

        if self.payment_method == CHARGEBEE and self.subscription_id:
            metadata = get_subscription_metadata(self.subscription_id)
        elif self.payment_method == XERO and self.subscription_id:
            metadata = XeroSubscriptionMetadata(
                seats=self.max_seats, api_calls=self.max_api_calls, projects=None
            )

        if not metadata:
            metadata = BaseSubscriptionMetadata(
                seats=self.max_seats,
                api_calls=self.max_api_calls,
                projects=MAX_PROJECTS_IN_FREE_PLAN,
            )

        return metadata

    def add_single_seat(self):
        if not self.can_auto_upgrade_seats:
            raise SubscriptionDoesNotSupportSeatUpgrade()

        add_single_seat(self.subscription_id)


class OrganisationWebhook(AbstractBaseExportableWebhookModel):
    name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="webhooks"
    )

    class Meta:
        ordering = ("id",)  # explicit ordering to prevent pagination warnings


class OrganisationSubscriptionInformationCache(models.Model):
    """
    Model to hold a cache of an organisation's API usage and their Chargebee plan limits.
    """

    organisation = models.OneToOneField(
        Organisation,
        related_name="subscription_information_cache",
        on_delete=models.CASCADE,
    )
    updated_at = models.DateTimeField(auto_now=True)

    api_calls_24h = models.IntegerField(default=0)
    api_calls_7d = models.IntegerField(default=0)
    api_calls_30d = models.IntegerField(default=0)

    allowed_seats = models.IntegerField(default=1)
    allowed_30d_api_calls = models.IntegerField(default=50000)

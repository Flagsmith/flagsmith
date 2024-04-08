# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from core.models import SoftDeleteExportableModel
from django.conf import settings
from django.core.cache import caches
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django_lifecycle import (
    AFTER_CREATE,
    AFTER_SAVE,
    BEFORE_DELETE,
    LifecycleModelMixin,
    hook,
)
from simple_history.models import HistoricalRecords

from app.utils import is_enterprise, is_saas
from integrations.lead_tracking.hubspot.tasks import (
    track_hubspot_lead,
    update_hubspot_active_subscription,
)
from organisations.chargebee import (
    get_customer_id_from_subscription_id,
    get_max_api_calls_for_plan,
    get_max_seats_for_plan,
    get_plan_meta_data,
    get_portal_url,
    get_subscription_metadata_from_id,
)
from organisations.chargebee.chargebee import add_single_seat
from organisations.chargebee.chargebee import (
    cancel_subscription as cancel_chargebee_subscription,
)
from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.subscriptions.constants import (
    CHARGEBEE,
    FREE_PLAN_ID,
    FREE_PLAN_SUBSCRIPTION_METADATA,
    MAX_API_CALLS_IN_FREE_PLAN,
    MAX_SEATS_IN_FREE_PLAN,
    SUBSCRIPTION_BILLING_STATUSES,
    SUBSCRIPTION_PAYMENT_METHODS,
    TRIAL_SUBSCRIPTION_ID,
    XERO,
)
from organisations.subscriptions.exceptions import (
    SubscriptionDoesNotSupportSeatUpgrade,
)
from organisations.subscriptions.metadata import BaseSubscriptionMetadata
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata
from users.utils.mailer_lite import MailerLite
from webhooks.models import AbstractBaseExportableWebhookModel

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
    force_2fa = models.BooleanField(default=False)

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

    def has_paid_subscription(self) -> bool:
        # Includes subscriptions that are canceled.
        # See is_paid for active paid subscriptions only.
        return hasattr(self, "subscription") and bool(self.subscription.subscription_id)

    def has_subscription_information_cache(self) -> bool:
        return hasattr(self, "subscription_information_cache") and bool(
            self.subscription_information_cache
        )

    @property
    def is_paid(self):
        return (
            self.has_paid_subscription() and self.subscription.cancellation_date is None
        )

    def over_plan_seats_limit(self, additional_seats: int = 0):
        if self.has_paid_subscription():
            susbcription_metadata = self.subscription.get_subscription_metadata()
            return self.num_seats + additional_seats > susbcription_metadata.seats

        return self.num_seats + additional_seats > getattr(
            self.subscription, "max_seats", MAX_SEATS_IN_FREE_PLAN
        )

    def reset_alert_status(self):
        self.alerted_over_plan_limit = False
        self.save()

    def is_auto_seat_upgrade_available(self) -> bool:
        return (
            len(settings.AUTO_SEAT_UPGRADE_PLANS) > 0
            and self.subscription.can_auto_upgrade_seats
        )

    @hook(BEFORE_DELETE)
    def cancel_subscription(self):
        if self.has_paid_subscription():
            self.subscription.prepare_for_cancel()

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

    @hook(AFTER_SAVE, when="stop_serving_flags", has_changed=True)
    def rebuild_environments(self):
        # Avoid circular imports.
        from environments.models import Environment
        from environments.tasks import rebuild_environment_document

        for environment_id in Environment.objects.filter(
            project__organisation=self
        ).values_list("id", flat=True):
            rebuild_environment_document.delay(args=(environment_id,))

    def cancel_users(self):
        remaining_seat_holder = (
            UserOrganisation.objects.filter(
                organisation=self,
                role=OrganisationRole.ADMIN,
            )
            .order_by("date_joined")
            .first()
        )

        UserOrganisation.objects.filter(
            organisation=self,
        ).exclude(id=remaining_seat_holder.id).delete()


class UserOrganisation(LifecycleModelMixin, models.Model):
    user = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=50, choices=OrganisationRole.choices)

    class Meta:
        unique_together = (
            "user",
            "organisation",
        )

    @hook(AFTER_CREATE)
    def register_hubspot_lead_tracking(self):
        if settings.ENABLE_HUBSPOT_LEAD_TRACKING:
            track_hubspot_lead.delay(
                args=(
                    self.user.id,
                    self.organisation.id,
                )
            )


class Subscription(LifecycleModelMixin, SoftDeleteExportableModel):
    # Even though it is not enforced at the database level,
    # every organisation has a subscription.
    organisation = models.OneToOneField(
        Organisation, on_delete=models.CASCADE, related_name="subscription"
    )
    subscription_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_date = models.DateTimeField(blank=True, null=True)
    plan = models.CharField(max_length=100, null=True, blank=True, default=FREE_PLAN_ID)
    max_seats = models.IntegerField(default=MAX_SEATS_IN_FREE_PLAN)
    max_api_calls = models.BigIntegerField(default=MAX_API_CALLS_IN_FREE_PLAN)
    cancellation_date = models.DateTimeField(blank=True, null=True)
    customer_id = models.CharField(max_length=100, blank=True, null=True)

    # Free and cancelled subscriptions are blank.
    billing_status = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_BILLING_STATUSES,
        blank=True,
        null=True,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_PAYMENT_METHODS,
        blank=True,
        null=True,
    )
    notes = models.CharField(max_length=500, blank=True, null=True)

    # Intentionally avoid the AuditLog for subscriptions.
    history = HistoricalRecords()

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

    @property
    def is_free_plan(self) -> bool:
        return self.plan == FREE_PLAN_ID

    @hook(AFTER_SAVE, when="plan", has_changed=True)
    def update_hubspot_active_subscription(self):
        if not settings.ENABLE_HUBSPOT_LEAD_TRACKING:
            return

        update_hubspot_active_subscription.delay(args=(self.id,))

    @hook(AFTER_SAVE, when="cancellation_date", has_changed=True)
    @hook(AFTER_SAVE, when="subscription_id", has_changed=True)
    def update_mailer_lite_subscribers(self):
        if settings.MAILERLITE_API_KEY:
            mailer_lite = MailerLite()
            mailer_lite.update_organisation_users(self.organisation.id)

    def save_as_free_subscription(self):
        """
        Wipes a subscription to a normal free plan.

        The only normal field that is retained is the notes field.
        """
        self.subscription_id = None
        self.subscription_date = None
        self.plan = FREE_PLAN_ID
        self.max_seats = MAX_SEATS_IN_FREE_PLAN
        self.max_api_calls = MAX_API_CALLS_IN_FREE_PLAN
        self.cancellation_date = None
        self.customer_id = None
        self.billing_status = None
        self.payment_method = None

        self.save()

        if not getattr(self.organisation, "subscription_information_cache", None):
            return

        # There is a weird bug where the cache is present, but the id is unset.
        # See here for more: https://flagsmith.sentry.io/issues/4945988284/
        if not self.organisation.subscription_information_cache.id:
            return

        self.organisation.subscription_information_cache.delete()

    def prepare_for_cancel(
        self, cancellation_date=timezone.now(), update_chargebee=True
    ) -> None:
        """
        This method get's a subscription ready for cancelation.

        If cancellation_date is in the future some aspects are
        reserved for a task after the date has passed.
        """
        # Avoid circular import.
        from organisations.tasks import send_org_subscription_cancelled_alert

        if self.payment_method == CHARGEBEE and update_chargebee:
            cancel_chargebee_subscription(self.subscription_id)

        send_org_subscription_cancelled_alert.delay(
            kwargs={
                "organisation_name": self.organisation.name,
                "formatted_cancellation_date": cancellation_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )

        if cancellation_date <= timezone.now():
            # Since the date is immediate, wipe data right away.
            self.organisation.cancel_users()
            self.save_as_free_subscription()
            return

        # Since the date is in the future, a task takes it.
        self.cancellation_date = cancellation_date
        self.billing_status = None
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

    def get_subscription_metadata(self) -> BaseSubscriptionMetadata:
        if self.is_free_plan:
            # Free plan is the default everywhere, we should prevent
            # increased access for all deployment types on the free
            # plan.
            return FREE_PLAN_SUBSCRIPTION_METADATA

        return (
            self._get_subscription_metadata_for_saas()
            if is_saas()
            else self._get_subscription_metadata_for_self_hosted()
        )

    def _get_subscription_metadata_for_saas(self) -> BaseSubscriptionMetadata:
        if self.payment_method == CHARGEBEE and self.subscription_id:
            return self._get_subscription_metadata_for_chargebee()
        elif self.payment_method == XERO and self.subscription_id:
            return XeroSubscriptionMetadata(
                seats=self.max_seats, api_calls=self.max_api_calls
            )

        # Default fall through here means this is a manually added subscription
        # or for a payment method that is not covered above. In this situation
        # we want the response to be what is stored in the Django database.
        # Note that Free plans are caught in the parent method above.
        return BaseSubscriptionMetadata(
            seats=self.max_seats, api_calls=self.max_api_calls
        )

    def _get_subscription_metadata_for_chargebee(self) -> ChargebeeObjMetadata:
        if self.organisation.has_subscription_information_cache():
            # Getting the data from the subscription information cache because
            # data is guaranteed to be up to date by using a Chargebee webhook.
            return ChargebeeObjMetadata(
                seats=self.organisation.subscription_information_cache.allowed_seats,
                api_calls=self.organisation.subscription_information_cache.allowed_30d_api_calls,
                projects=self.organisation.subscription_information_cache.allowed_projects,
                chargebee_email=self.organisation.subscription_information_cache.chargebee_email,
            )

        return get_subscription_metadata_from_id(self.subscription_id)

    def _get_subscription_metadata_for_self_hosted(self) -> BaseSubscriptionMetadata:
        if not is_enterprise():
            return FREE_PLAN_SUBSCRIPTION_METADATA

        return BaseSubscriptionMetadata(
            seats=self.max_seats,
            api_calls=self.max_api_calls,
            projects=None,
        )

    def add_single_seat(self):
        if not self.can_auto_upgrade_seats:
            raise SubscriptionDoesNotSupportSeatUpgrade()

        add_single_seat(self.subscription_id)

    def get_api_call_overage(self):
        subscription_info = self.organisation.subscription_information_cache
        overage = (
            subscription_info.api_calls_30d - subscription_info.allowed_30d_api_calls
        )
        return overage if overage > 0 else 0

    def is_in_trial(self) -> bool:
        return self.subscription_id == TRIAL_SUBSCRIPTION_ID


class OrganisationWebhook(AbstractBaseExportableWebhookModel):
    name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="webhooks"
    )
    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)

    class Meta:
        ordering = ("id",)  # explicit ordering to prevent pagination warnings


class OrganisationSubscriptionInformationCache(LifecycleModelMixin, models.Model):
    """
    Model to hold a cache of an organisation's API usage and their Chargebee plan limits.
    """

    organisation = models.OneToOneField(
        Organisation,
        related_name="subscription_information_cache",
        on_delete=models.CASCADE,
    )
    updated_at = models.DateTimeField(auto_now=True)
    chargebee_updated_at = models.DateTimeField(auto_now=False, null=True)
    influx_updated_at = models.DateTimeField(auto_now=False, null=True)
    current_billing_term_starts_at = models.DateTimeField(auto_now=False, null=True)
    current_billing_term_ends_at = models.DateTimeField(auto_now=False, null=True)

    api_calls_24h = models.IntegerField(default=0)
    api_calls_7d = models.IntegerField(default=0)
    api_calls_30d = models.IntegerField(default=0)

    allowed_seats = models.IntegerField(default=1)
    allowed_30d_api_calls = models.IntegerField(default=50000)
    allowed_projects = models.IntegerField(default=1, blank=True, null=True)

    chargebee_email = models.EmailField(blank=True, max_length=254, null=True)

    @hook(AFTER_SAVE, when="allowed_30d_api_calls", has_changed=True)
    def erase_api_notifications(self):
        self.organisation.api_usage_notifications.all().delete()


class OranisationAPIUsageNotification(models.Model):
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="api_usage_notifications"
    )
    percent_usage = models.IntegerField(
        null=False,
        validators=[MinValueValidator(75), MaxValueValidator(120)],
    )
    notified_at = models.DateTimeField(null=True)

    created_at = models.DateTimeField(null=True, auto_now_add=True)
    updated_at = models.DateTimeField(null=True, auto_now=True)


class HubspotOrganisation(models.Model):
    organisation = models.OneToOneField(
        Organisation,
        related_name="hubspot_organisation",
        on_delete=models.CASCADE,
    )
    hubspot_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

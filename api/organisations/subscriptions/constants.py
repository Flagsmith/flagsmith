from enum import Enum

from django.conf import settings

from organisations.subscriptions.metadata import BaseSubscriptionMetadata

MAX_SEATS_IN_FREE_PLAN = 1
MAX_API_CALLS_IN_FREE_PLAN = 50000
SUBSCRIPTION_DEFAULT_LIMITS = (
    MAX_API_CALLS_IN_FREE_PLAN,
    MAX_SEATS_IN_FREE_PLAN,
    settings.MAX_PROJECTS_IN_FREE_PLAN,
)

CHARGEBEE = "CHARGEBEE"
XERO = "XERO"
AWS_MARKETPLACE = "AWS_MARKETPLACE"
SUBSCRIPTION_PAYMENT_METHODS = [
    (CHARGEBEE, "Chargebee"),
    (XERO, "Xero"),
    (AWS_MARKETPLACE, "AWS Marketplace"),
]


# Active means payments for the subscription are being processed
# without issue, dunning means the subscription is still ongoing
# but payments for one or more of the invoices are being retried.
SUBSCRIPTION_BILLING_STATUS_ACTIVE = "ACTIVE"
SUBSCRIPTION_BILLING_STATUS_DUNNING = "DUNNING"
SUBSCRIPTION_BILLING_STATUSES = [
    (SUBSCRIPTION_BILLING_STATUS_ACTIVE, "Active"),
    (SUBSCRIPTION_BILLING_STATUS_DUNNING, "Dunning"),
]


FREE_PLAN_SUBSCRIPTION_METADATA = BaseSubscriptionMetadata(
    seats=MAX_SEATS_IN_FREE_PLAN,
    api_calls=MAX_API_CALLS_IN_FREE_PLAN,
    projects=settings.MAX_PROJECTS_IN_FREE_PLAN,
)
FREE_PLAN_ID = "free"
TRIAL_SUBSCRIPTION_ID = "trial"
SCALE_UP = "scale-up"
SCALE_UP_12_MONTHS_V2 = "scale-up-12-months-v2"
SCALE_UP_QUARTERLY_V2_SEMIANNUAL = "scale-up-quarterly-v2-semiannual"
SCALE_UP_V2 = "scale-up-v2"
STARTUP = "startup"
STARTUP_ANNUAL_V2 = "startup-annual-v2"
STARTUP_V2 = "startup-v2"


class SubscriptionCacheEntity(Enum):
    INFLUX = "INFLUX"
    CHARGEBEE = "CHARGEBEE"

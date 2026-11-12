from datetime import timedelta

from organisations.subscriptions.constants import SubscriptionPlanFamily

API_USAGE_ALERT_THRESHOLDS = [75, 90, 100, 120, 200, 300, 400, 500]
API_USAGE_GRACE_PERIOD = 7
ALERT_EMAIL_MESSAGE = (
    "Organisation %s has used %d seats which is over their plan limit of %d (plan: %s)"
)
ALERT_EMAIL_SUBJECT = "Organisation over number of seats"
OVERAGE_BILLING_PLAN_FAMILIES = (
    SubscriptionPlanFamily.START_UP,
    SubscriptionPlanFamily.SCALE_UP,
)
OVERAGE_BILLING_MIN_TERM = timedelta(days=25)
OVERAGE_BILLING_MAX_TERM = timedelta(days=35)

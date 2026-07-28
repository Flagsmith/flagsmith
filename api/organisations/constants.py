from datetime import timedelta

API_USAGE_ALERT_THRESHOLDS = [75, 90, 100, 120, 200, 300, 400, 500]
API_USAGE_GRACE_PERIOD = 7
# Chargebee plan limits are refreshed every 6h (see
# `update_organisation_subscription_information_cache_recurring`). Anything
# older than 2x that means the sync is failing, not just due for its next run.
CHARGEBEE_CACHE_STALE_AFTER = timedelta(hours=12)
ALERT_EMAIL_MESSAGE = (
    "Organisation %s has used %d seats which is over their plan limit of %d (plan: %s)"
)
ALERT_EMAIL_SUBJECT = "Organisation over number of seats"

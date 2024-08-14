from organisations.subscriptions.constants import SubscriptionPlanFamily

# Constants to define how many days worth of version history should be
# returned in the list endpoint based on the plan of the requesting organisation.
DEFAULT_VERSION_LIMIT_DAYS = 7
START_UP_VERSION_LIMIT_DAYS = DEFAULT_VERSION_LIMIT_DAYS
SCALE_UP_VERSION_LIMIT_DAYS = DEFAULT_VERSION_LIMIT_DAYS

VERSION_LIMIT_DAYS_BY_PLAN = {
    SubscriptionPlanFamily.FREE: DEFAULT_VERSION_LIMIT_DAYS,
    SubscriptionPlanFamily.START_UP: START_UP_VERSION_LIMIT_DAYS,
    SubscriptionPlanFamily.SCALE_UP: SCALE_UP_VERSION_LIMIT_DAYS,
    SubscriptionPlanFamily.ENTERPRISE: None,  # No limit
}

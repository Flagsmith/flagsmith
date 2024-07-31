from organisations.subscriptions.constants import SubscriptionPlanFamily

# Constants to define how many versions should be returned in the list endpoint
# based on the plan of the requesting organisation.
DEFAULT_VERSION_LIMIT = 3
# extra is used to return extra values that the FE can blur out
EXTRA = 1
VERSION_LIMIT_BY_PLAN = {
    SubscriptionPlanFamily.FREE: DEFAULT_VERSION_LIMIT + EXTRA,
    SubscriptionPlanFamily.START_UP: DEFAULT_VERSION_LIMIT + EXTRA,
    SubscriptionPlanFamily.SCALE_UP: 5 + EXTRA,
    SubscriptionPlanFamily.ENTERPRISE: None,  # No limit
}

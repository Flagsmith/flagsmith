from organisations.subscriptions.constants import SubscriptionPlanFamily

# Constants to define how many versions should be returned in the list endpoint
# based on the plan of the requesting organisation.
DEFAULT_VERSION_LIMIT = 3
START_UP_VERSION_LIMIT = DEFAULT_VERSION_LIMIT
SCALE_UP_VERSION_LIMIT = 5

# extra is used to return extra values that the FE can blur out
EXTRA_VERSIONS_FOR_LIST = 1

VERSION_LIMIT_BY_PLAN = {
    SubscriptionPlanFamily.FREE: DEFAULT_VERSION_LIMIT,
    SubscriptionPlanFamily.START_UP: DEFAULT_VERSION_LIMIT,
    SubscriptionPlanFamily.SCALE_UP: SCALE_UP_VERSION_LIMIT,
    SubscriptionPlanFamily.ENTERPRISE: None,  # No limit
}

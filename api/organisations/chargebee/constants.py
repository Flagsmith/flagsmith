ADDITIONAL_API_START_UP_ADDON_ID = "additional-api-start-up-monthly"
ADDITIONAL_API_SCALE_UP_ADDON_ID = "additional-api-scale-up-monthly"

# The seat addon's ID is derived from the subscription's plan ID by prepending
# the addon name. For example:
# {plan_id} -> {addon_name_prefix}-{plan_id}
SEAT_ADDON_NAME_PREFIX_BY_PLAN_PREFIX: dict[str, str] = {
    "scaleupv4": "Additional-Team-Members",
}

SEAT_SCALE_UP_V2_ADDON_BY_BILLING_PERIOD: dict[int, str] = {
    1: "additional-team-members-scale-up-v2-monthly",
    6: "additional-team-members-scale-up-v2-semiannual",
    12: "additional-team-members-scale-up-v2-annual",
}

ADDITIONAL_API_START_UP_ADDON_ID = "additional-api-start-up-monthly"
ADDITIONAL_API_SCALE_UP_ADDON_ID = "additional-api-scale-up-monthly"

SEAT_ADDON_BY_PLAN_PREFIX: dict[str, str] = {
    "scaleupv4": "Additional-Team-Members-Scale-Up-v4",
}

SEAT_SCALE_UP_V2_ADDON_BY_BILLING_PERIOD: dict[int, str] = {
    1: "additional-team-members-scale-up-v2-monthly",
    6: "additional-team-members-scale-up-v2-semiannual",
    12: "additional-team-members-scale-up-v2-annual",
}

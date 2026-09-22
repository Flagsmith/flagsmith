ADDITIONAL_API_START_UP_ADDON_ID = "additional-api-start-up-monthly"
ADDITIONAL_API_SCALE_UP_ADDON_ID = "additional-api-scale-up-monthly"

SEAT_SCALE_UP_V2_ADDON_BY_BILLING_PERIOD: dict[tuple[int, str], str] = {
    (1, "month"): "additional-team-members-scale-up-v2-monthly",
    (6, "month"): "additional-team-members-scale-up-v2-semiannual",
    (12, "month"): "additional-team-members-scale-up-v2-annual",
    (1, "year"): "additional-team-members-scale-up-v2-annual",
}

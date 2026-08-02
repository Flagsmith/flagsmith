import prometheus_client

flagsmith_oauth2_dcr_registrations_total = prometheus_client.Counter(
    "flagsmith_oauth2_dcr_registrations_total",
    "Total OAuth2 dynamic client registration requests, labelled by the "
    "requested token endpoint auth method and whether the registration "
    "was accepted or rejected.",
    ["token_endpoint_auth_method", "outcome"],
)

flagsmith_oauth2_cimd_resolutions_total = prometheus_client.Counter(
    "flagsmith_oauth2_cimd_resolutions_total",
    "Total OAuth2 CIMD (Client ID Metadata Document) resolution attempts, "
    "labelled by whether the resolution was accepted or rejected.",
    ["outcome"],
)

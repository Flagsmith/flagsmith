import prometheus_client

flagsmith_oauth2_dcr_registrations_total = prometheus_client.Counter(
    "flagsmith_oauth2_dcr_registrations_total",
    "Total OAuth2 dynamic client registration requests, labelled by the "
    "requested token endpoint auth method and whether the registration "
    "was accepted or rejected.",
    ["token_endpoint_auth_method", "outcome"],
)

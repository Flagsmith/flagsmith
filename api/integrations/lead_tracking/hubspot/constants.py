HUBSPOT_COOKIE_NAME = "hubspotutk"
HUBSPOT_PORTAL_ID = "143451822"
HUBSPOT_FORM_ID_SAAS = "562ee023-fb3f-4645-a217-4d8c9b4e45be"
HUBSPOT_FORM_ID_SELF_HOSTED = "e79b8eca-a727-4188-a5ed-8f71c707ac50"
HUBSPOT_ROOT_FORM_URL = "https://api.hsforms.com/submissions/v3/integration/submit"
HUBSPOT_API_LEAD_SOURCE_SELF_HOSTED = "self-hosted"
HUBSPOT_ACTIVE_SUBSCRIPTION_SELF_HOSTED = "free-opensource"

# Personal email providers - users signing up with these do not identify a unique
# company in HubSpot, so we skip the organisation-id write for them.
GENERIC_EMAIL_DOMAINS = frozenset(
    {
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "outlook.com",
        "icloud.com",
        "protonmail.com",
        "proton.me",
        "mail.com",
        "aol.com",
        "live.com",
        "me.com",
        "yandex.com",
        "gmx.com",
    }
)

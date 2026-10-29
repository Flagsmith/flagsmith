EVENT_NAMES_LIMIT = 500
EVENT_NAMES_CACHE_SECONDS = 300
CUSTOMER_EVENT_STATS_CACHE_SECONDS = 60
CUSTOMER_EVENT_NAMES_FAILURE_CACHE_SECONDS = 60

VERIFY_TIMEOUT_SECONDS = 5
EVENT_NAMES_TIMEOUT_SECONDS = 15
BACKGROUND_QUERY_TIMEOUT_SECONDS = 120

MISSING_EVENTS_TABLE_DETAIL = (
    "Events table not found in the configured database. Run the setup SQL to create it."
)
SCHEMA_MISMATCH_DETAIL = "The events table's columns don't match the setup SQL."
PERMISSION_DENIED_DETAIL = (
    "Permission denied on the events table. The user needs SELECT and INSERT on it."
)
QUERY_TIMEOUT_DETAIL = "The query timed out."

FLAGSMITH_DATABASE_SOURCE = "flagsmith_database"
FLAGSMITH_DATABASE_SCHEMA = "flagsmith_exp"
FLAGSMITH_DATABASE_UNAVAILABLE_DETAIL = "The Flagsmith database can only be used as a warehouse on self-hosted PostgreSQL installations."
FLAGSMITH_DATABASE_MISSING_EVENTS_TABLE_DETAIL = "The events table is missing from the Flagsmith database. Run the database migrations to create it."
FLAGSMITH_DATABASE_PERMISSION_DENIED_DETAIL = "Permission denied on the events table. Flagsmith's database user needs SELECT on it."

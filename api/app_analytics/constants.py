from typing import get_args

from app_analytics.types import Label, PeriodType

ANALYTICS_READ_BUCKET_SIZE = 15

# get_usage_data() related period constants
CURRENT_BILLING_PERIOD: PeriodType
PREVIOUS_BILLING_PERIOD: PeriodType
NINETY_DAY_PERIOD: PeriodType
(
    CURRENT_BILLING_PERIOD,
    PREVIOUS_BILLING_PERIOD,
    NINETY_DAY_PERIOD,
) = get_args(PeriodType)

# Optional headers sent from client SDK mapped to their respetive labels.
TRACK_HEADERS: dict[str, Label] = {
    "Flagsmith-Application-Name": "client_application_name",
    "Flagsmith-Application-Version": "client_application_version",
    "User-Agent": "user_agent",
}
LABELS: tuple[Label, ...] = get_args(Label)

NO_ANALYTICS_DATABASE_CONFIGURED_WARNING = (
    "No analytics database configured. "
    "Please set `USE_POSTGRES_FOR_ANALYTICS` or `INFLUXDB_TOKEN` in settings."
)

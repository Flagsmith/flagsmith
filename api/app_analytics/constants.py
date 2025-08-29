from typing import get_args

from app_analytics.types import InputLabel, Label, PeriodType

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


SDK_USER_AGENT_KNOWN_VERSIONS = {
    "flagsmith-dotnet-sdk": ["unknown"],
    "flagsmith-elixir-sdk": ["unknown"],
    "flagsmith-flutter-sdk": ["unknown"],
    "flagsmith-go-sdk": ["unknown"],
    "flagsmith-java-sdk": ["unknown"],
    "flagsmith-js-sdk": [
        "unknown",
        "9.3.1",
    ],
    "flagsmith-kotlin-android-sdk": ["unknown"],
    "flagsmith-nodejs-sdk": ["unknown"],
    "flagsmith-php-sdk": ["unknown"],
    "flagsmith-python-sdk": ["unknown"],
    "flagsmith-ruby-sdk": ["unknown"],
    "flagsmith-rust-sdk": ["unknown"],
    "flagsmith-swift-ios-sdk": ["unknown"],
}


# Optional headers sent from client SDK mapped to their respective labels.
TRACK_HEADERS: dict[str, InputLabel] = {
    "Flagsmith-Application-Name": "client_application_name",
    "Flagsmith-Application-Version": "client_application_version",
    "Flagsmith-SDK-User-Agent": "sdk_user_agent",
    "User-Agent": "user_agent",
}
LABELS: tuple[str, ...] = tuple(str(label) for label in get_args(Label))

NO_ANALYTICS_DATABASE_CONFIGURED_WARNING = (
    "No analytics database configured. "
    "Please set `USE_POSTGRES_FOR_ANALYTICS` or `INFLUXDB_TOKEN` in settings."
)

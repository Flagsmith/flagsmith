from typing import get_args

from app_analytics.types import InputLabel, KnownSDK, Label, PeriodType

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


# We make sure to only track known SDK versions
# because, when we prepare the data for Influx, we need to map to numeric IDs.
# This allows us to efficiently store usage and evaluation data.
SDK_USER_AGENT_KNOWN_VERSIONS: dict[KnownSDK, list[str]] = {
    "flagsmith-dotnet-sdk": [
        "unknown",
        "9.0.0",
    ],
    "flagsmith-elixir-sdk": [
        "unknown",
        "2.3.0",
        "2.3.1",
    ],
    "flagsmith-flutter-sdk": [
        "unknown",
        "6.1.0",
    ],
    "flagsmith-go-sdk": [
        "unknown",
        "5.0.0",
    ],
    "flagsmith-java-sdk": [
        "unknown",
        "8.0.0",
    ],
    "flagsmith-js-sdk": [
        "unknown",
        "9.3.1",
        "10.0.0",
    ],
    "flagsmith-kotlin-android-sdk": ["unknown"],
    "flagsmith-nodejs-sdk": [
        "unknown",
        "6.2.0",
        "7.0.2",
    ],
    "flagsmith-php-sdk": [
        "unknown",
        "5.0.0",
    ],
    "flagsmith-python-sdk": [
        "unknown",
        "5.0.0",
        "5.0.1",
        "5.0.2",
        "5.0.3",
    ],
    "flagsmith-ruby-sdk": [
        "unknown",
        "5.0.0",
    ],
    "flagsmith-rust-sdk": [
        "unknown",
        "2.1.0",
    ],
    "flagsmith-swift-ios-sdk": ["unknown"],
}

SDK_USER_AGENT_INFLUX_IDS: list[tuple[KnownSDK, int]] = [
    ("flagsmith-dotnet-sdk", 0),
    ("flagsmith-elixir-sdk", 10000),
    ("flagsmith-flutter-sdk", 20000),
    ("flagsmith-go-sdk", 30000),
    ("flagsmith-java-sdk", 40000),
    ("flagsmith-js-sdk", 50000),
    ("flagsmith-kotlin-android-sdk", 60000),
    ("flagsmith-nodejs-sdk", 70000),
    ("flagsmith-php-sdk", 80000),
    ("flagsmith-python-sdk", 90000),
    ("flagsmith-ruby-sdk", 100000),
    ("flagsmith-rust-sdk", 110000),
    ("flagsmith-swift-ios-sdk", 120000),
]


SDK_USER_AGENTS_BY_INFLUX_ID: dict[int, str] = {}
SDK_INFLUX_IDS_BY_USER_AGENT: dict[str, int] = {}

for sdk_name, sdk_id in SDK_USER_AGENT_INFLUX_IDS:
    for version_index, version in enumerate(SDK_USER_AGENT_KNOWN_VERSIONS[sdk_name]):
        influx_id = sdk_id + version_index
        user_agent = f"{sdk_name}/{version}"
        SDK_USER_AGENTS_BY_INFLUX_ID[influx_id] = user_agent
        SDK_INFLUX_IDS_BY_USER_AGENT[user_agent] = influx_id


# Optional headers sent from client SDK mapped to their respective labels.
TRACK_HEADERS: dict[str, InputLabel] = {
    "Flagsmith-Application-Name": "client_application_name",
    "Flagsmith-Application-Version": "client_application_version",
    "Flagsmith-SDK-User-Agent": "sdk_user_agent",
    "User-Agent": "user_agent",
}
LABELS: tuple[Label, ...] = get_args(Label)

NO_ANALYTICS_DATABASE_CONFIGURED_WARNING = (
    "No analytics database configured. "
    "Please set `USE_POSTGRES_FOR_ANALYTICS` or `INFLUXDB_TOKEN` in settings."
)

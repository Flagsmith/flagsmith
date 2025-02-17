import logging
import typing
from collections import defaultdict
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from influxdb_client import InfluxDBClient, Point  # type: ignore[import-untyped]
from influxdb_client.client.exceptions import InfluxDBError  # type: ignore[import-untyped]
from influxdb_client.client.write_api import SYNCHRONOUS  # type: ignore[import-untyped]
from sentry_sdk import capture_exception
from urllib3 import Retry
from urllib3.exceptions import HTTPError

from .dataclasses import FeatureEvaluationData, UsageData
from .influxdb_schema import FeatureEvaluationDataSchema, UsageDataSchema

logger = logging.getLogger(__name__)

url = settings.INFLUXDB_URL
token = settings.INFLUXDB_TOKEN
influx_org = settings.INFLUXDB_ORG
read_bucket = settings.INFLUXDB_BUCKET + "_downsampled_15m"

retries = Retry(connect=3, read=3, redirect=3)
# Set a timeout to prevent threads being potentially stuck open due to network weirdness
influxdb_client = InfluxDBClient(
    url=url, token=token, org=influx_org, retries=retries, timeout=3000
)

DEFAULT_DROP_COLUMNS = (
    "organisation",
    "organisation_id",
    "type",
    "project",
    "project_id",
    "environment",
    "environment_id",
    "host",
)


def get_range_bucket_mappings(date_start: datetime) -> str:
    now = timezone.now()
    if (now - date_start).days > 10:
        return settings.INFLUXDB_BUCKET + "_downsampled_1h"  # type: ignore[no-any-return]
    return settings.INFLUXDB_BUCKET + "_downsampled_15m"  # type: ignore[no-any-return]


class InfluxDBWrapper:
    def __init__(self, name):  # type: ignore[no-untyped-def]
        self.name = name
        self.records = []
        self.write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

    def add_data_point(self, field_name, field_value, tags=None):  # type: ignore[no-untyped-def]
        point = Point(self.name)
        point.field(field_name, field_value)

        if tags is not None:
            for tag_key, tag_value in tags.items():
                point = point.tag(tag_key, tag_value)

        self.records.append(point)

    def write(self):  # type: ignore[no-untyped-def]
        try:
            self.write_api.write(bucket=settings.INFLUXDB_BUCKET, record=self.records)
        except (HTTPError, InfluxDBError) as e:
            logger.warning(
                "Failed to write records to Influx: %s",
                str(e),
                exc_info=e,
            )
            logger.debug(
                "Records: %s. Bucket: %s",
                self.records,
                settings.INFLUXDB_BUCKET,
            )

    @staticmethod
    def influx_query_manager(  # type: ignore[no-untyped-def]
        date_start: datetime | None = None,
        date_stop: datetime | None = None,
        drop_columns: typing.Tuple[str, ...] = DEFAULT_DROP_COLUMNS,
        filters: str = "|> filter(fn:(r) => r._measurement == 'api_call')",
        extra: str = "",
        bucket: str = read_bucket,
    ):
        now = timezone.now()
        if date_start is None:
            date_start = now - timedelta(days=30)

        if date_stop is None:
            date_stop = now

        # Influx throws an error for an empty range, so just return a list.
        if date_start == date_stop:
            return []

        query_api = influxdb_client.query_api()
        drop_columns_input = str(list(drop_columns)).replace("'", '"')

        query = (
            f'from(bucket:"{bucket}")'
            f" |> range(start: {date_start.isoformat()}, stop: {date_stop.isoformat()})"
            f" {filters}"
            f" |> drop(columns: {drop_columns_input})"
            f"{extra}"
        )
        logger.debug("Running query in influx: \n\n %s", query)

        try:
            result = query_api.query(org=influx_org, query=query)
            return result
        except HTTPError as e:
            capture_exception(e)
            return []


def get_events_for_organisation(
    organisation_id: id,  # type: ignore[valid-type]
    date_start: datetime | None = None,
    date_stop: datetime | None = None,
) -> int:
    """
    Query influx db for usage for given organisation id

    :param organisation_id: an id of the organisation to get usage for
    :return: a number of request counts for organisation
    """
    now = timezone.now()
    if date_start is None:
        date_start = now - timedelta(days=30)

    if date_stop is None:
        date_stop = now

    result = InfluxDBWrapper.influx_query_manager(
        filters=build_filter_string(
            [
                'r._measurement == "api_call"',
                'r["_field"] == "request_count"',
                f'r["organisation_id"] == "{organisation_id}"',
            ]
        ),
        drop_columns=(
            "organisation",
            "project",
            "project_id",
            "environment",
            "environment_id",
        ),
        extra="|> sum()",
        date_start=date_start,
        date_stop=date_stop,
    )

    total = 0
    for table in result:
        for record in table.records:
            total += record.get_value()

    return total


def get_event_list_for_organisation(
    organisation_id: int,
    date_start: datetime | None = None,
    date_stop: datetime | None = None,
) -> tuple[dict[str, list[int]], list[str]]:
    """
    Query influx db for usage for given organisation id

    :param organisation_id: an id of the organisation to get usage for

    :return: a number of request counts for organisation in chart.js scheme
    """
    now = timezone.now()
    if date_start is None:
        date_start = now - timedelta(days=30)

    if date_stop is None:
        date_stop = now

    results = InfluxDBWrapper.influx_query_manager(
        filters=f'|> filter(fn:(r) => r._measurement == "api_call") \
                  |> filter(fn: (r) => r["organisation_id"] == "{organisation_id}")',
        extra='|> aggregateWindow(every: 24h, fn: sum, timeSrc: "_start")',
        date_start=date_start,
        date_stop=date_stop,
    )
    dataset = defaultdict(list)
    labels = []  # type: ignore[var-annotated]

    date_difference = date_stop - date_start
    required_records = date_difference.days + 1
    for result in results:
        for record in result.records:
            dataset[record["resource"]].append(record["_value"])
            if len(labels) != required_records:
                labels.append(record.values["_time"].strftime("%Y-%m-%d"))
    return dataset, labels


def get_multiple_event_list_for_organisation(
    organisation_id: int,
    project_id: int = None,  # type: ignore[assignment]
    environment_id: int = None,  # type: ignore[assignment]
    date_start: datetime | None = None,
    date_stop: datetime | None = None,
) -> list[UsageData]:
    """
    Query influx db for usage for given organisation id

    :param organisation_id: an id of the organisation to get usage for
    :param project_id: optionally filter by project id
    :param environment_id: optionally filter by an environment id

    :return: a number of requests for flags, traits, identities, environment-document
    """
    now = timezone.now()
    if date_start is None:
        date_start = now - timedelta(days=30)

    if date_stop is None:
        date_stop = now

    filters = [
        'r._measurement == "api_call"',
        f'r["organisation_id"] == "{organisation_id}"',
    ]

    if project_id:
        filters.append(f'r["project_id"] == "{project_id}"')

    if environment_id:
        filters.append(f'r["environment_id"] == "{environment_id}"')

    results = InfluxDBWrapper.influx_query_manager(
        date_start=date_start,
        date_stop=date_stop,
        filters=build_filter_string(filters),
        extra='|> aggregateWindow(every: 24h, fn: sum, timeSrc: "_start")',
    )
    if not results:
        return results  # type: ignore[no-any-return]

    dataset = [{} for _ in range(len(results[0].records))]  # type: ignore[var-annotated]

    for result in results:
        for i, record in enumerate(result.records):
            dataset[i][record.values["resource"].capitalize()] = record.values["_value"]
            dataset[i]["name"] = record.values["_time"].strftime("%Y-%m-%d")

    return dataset  # type: ignore[return-value]


def get_usage_data(
    organisation_id: int,
    project_id: int | None = None,
    environment_id: int | None = None,
    date_start: datetime | None = None,
    date_stop: datetime | None = None,
) -> list[UsageData]:
    now = timezone.now()
    if date_start is None:
        date_start = now - timedelta(days=30)

    if date_stop is None:
        date_stop = now

    events_list = get_multiple_event_list_for_organisation(
        organisation_id=organisation_id,
        project_id=project_id,  # type: ignore[arg-type]
        environment_id=environment_id,  # type: ignore[arg-type]
        date_start=date_start,
        date_stop=date_stop,
    )
    return UsageDataSchema(many=True).load(events_list)  # type: ignore[no-any-return,arg-type]


def get_multiple_event_list_for_feature(
    environment_id: int,
    feature_name: str,
    date_start: datetime | None = None,
    aggregate_every: str = "24h",
) -> list[dict]:  # type: ignore[type-arg]
    """
    Get aggregated request data for the given feature in a given environment across
    all time, aggregated into time windows of length defined by the period argument.

    Example data structure
    [
        {
            "first_feature_name": 13,  // feature name and number of requests
            "datetime": '2020-12-18'
        },
        {
            "first_feature_name": 15,
            "datetime": '2020-11-18'  // 30 days prior
        }
    ]

    :param environment_id: an id of the environment to get usage for
    :param feature_name: the name of the feature to get usage for
    :param date_start: the influx datetime period to filter on
    :param aggregate_every: the influx time period to aggregate the data by, e.g. 24h

    :return: a list of dicts with feature and request count in a specific environment
    """
    now = timezone.now()
    if date_start is None:
        date_start = now - timedelta(days=30)

    results = InfluxDBWrapper.influx_query_manager(
        date_start=date_start,
        filters=f'|> filter(fn:(r) => r._measurement == "feature_evaluation") \
                  |> filter(fn: (r) => r["_field"] == "request_count") \
                  |> filter(fn: (r) => r["environment_id"] == "{environment_id}") \
                  |> filter(fn: (r) => r["feature_id"] == "{feature_name}")',
        extra=f'|> aggregateWindow(every: {aggregate_every}, fn: sum, createEmpty: false, timeSrc: "_start") \
                   |> yield(name: "sum")',
    )
    if not results:
        return []

    dataset = [{} for _ in range(len(results[0].records))]  # type: ignore[var-annotated]

    # Iterating over Influx data looking for feature_id, and adding proper requests value and datetime to it
    # todo move it to marshmallow schema
    for result in results:
        for i, record in enumerate(result.records):
            dataset[i][record.values["feature_id"]] = record.values["_value"]
            dataset[i]["datetime"] = record.values["_time"].strftime("%Y-%m-%d")

    return dataset


def get_feature_evaluation_data(
    feature_name: str, environment_id: int, period: str = "30d"
) -> typing.List[FeatureEvaluationData]:
    assert period.endswith("d")
    days = int(period[:-1])
    date_start = timezone.now() - timedelta(days=days)
    data = get_multiple_event_list_for_feature(
        feature_name=feature_name,
        environment_id=environment_id,
        date_start=date_start,
    )
    return FeatureEvaluationDataSchema(many=True).load(data)  # type: ignore[no-any-return]


def get_top_organisations(
    date_start: datetime | None = None, limit: str = ""
) -> dict[int, int]:
    """
    Query influx db top used organisations

    :param date_start: Start of the date range for top organisations
    :param limit: limit for query


    :return: top organisations in descending order based on api calls.
    """
    now = timezone.now()
    if date_start is None:
        date_start = now - timedelta(days=30)

    if limit:
        limit = f"|> limit(n:{limit})"

    bucket = get_range_bucket_mappings(date_start)
    results = InfluxDBWrapper.influx_query_manager(
        date_start=date_start,
        bucket=bucket,
        filters='|> filter(fn:(r) => r._measurement == "api_call") \
                    |> filter(fn: (r) => r["_field"] == "request_count")',
        drop_columns=("_start", "_stop", "_time"),
        extra='|> group(columns: ["organisation"]) \
              |> sum() \
              |> group() \
              |> sort(columns: ["_value"], desc: true) '
        + limit,
    )

    dataset = {}

    for result in results:
        for record in result.records:
            try:
                org_id = int(record.values["organisation"].partition("-")[0])
                dataset[org_id] = record.get_value()
            except ValueError:
                logger.warning(
                    "Bad InfluxDB data found with organisation %s"
                    % record.values["organisation"].partition("-")[0]
                )

    return dataset


def get_current_api_usage(
    organisation_id: int, date_start: datetime | None = None
) -> int:
    """
    Query influx db for api usage

    :param organisation_id: filtered organisation
    :param date_range: data range for current api usage window

    :return: number of current api calls
    """
    now = timezone.now()
    if date_start is None:
        date_start = now - timedelta(days=30)

    bucket = read_bucket
    results = InfluxDBWrapper.influx_query_manager(
        date_start=date_start,
        bucket=bucket,
        filters=build_filter_string(
            [
                'r._measurement == "api_call"',
                'r["_field"] == "request_count"',
                f'r["organisation_id"] == "{organisation_id}"',
            ]
        ),
        drop_columns=("_start", "_stop", "_time"),
        extra='|> sum() \
               |> group() \
               |> sort(columns: ["_value"], desc: true) ',
    )

    for result in results:
        # Return zero if there are no API calls recorded.
        if len(result.records) == 0:
            return 0

        return sum(r.get_value() for r in result.records)

    return 0


def build_filter_string(filter_expressions: typing.List[str]) -> str:
    return "|> ".join(
        ["", *[f"filter(fn: (r) => {exp})" for exp in filter_expressions]]
    )

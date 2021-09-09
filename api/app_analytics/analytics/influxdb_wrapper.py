import typing
from collections import defaultdict

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

bucket = None
range_bucket_mappings = None
influxdb_client = None
org = None
read_bucket = None


class InfluxDBWrapper:
    def __init__(self, name):
        self.name = name
        self.records = []
        self.write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

    def add_data_point(self, field_name, field_value, tags=None):
        point = Point(self.name)
        point.field(field_name, field_value)

        if tags is not None:
            for tag_key, tag_value in tags.items():
                point = point.tag(tag_key, tag_value)

        self.records.append(point)

    def write(self):
        self.write_api.write(bucket=bucket, record=self.records)

    @staticmethod
    def influx_query_manager(
        date_range: str = "30d",
        date_stop: str = "now()",
        drop_columns: str = "'organisation', 'organisation_id', 'type', 'project', 'project_id'",
        filters: str = "|> filter(fn:(r) => r._measurement == 'api_call')",
        extra: str = "",
        read_bucket: str = "",
    ):
        query_api = influxdb_client.query_api()
        read_bucket = read_bucket or bucket + "_downsampled_15m"
        query = (
            f'from(bucket:"{read_bucket}")'
            f" |> range(start: -{date_range}, stop: {date_stop})"
            f" {filters}"
            f" |> drop(columns: [{drop_columns}])"
            f"{extra}"
        )

        result = query_api.query(org=org, query=query)
        return result


# def get_read_bucket():
#     return bucket + "_downsampled_15m"


def get_events_for_organisation(organisation_id: id, date_range: str = "30d"):
    """
    Query influx db for usage for given organisation id

    :param organisation_id: an id of the organisation to get usage for
    :return: a number of request counts for organisation
    """
    result = InfluxDBWrapper.influx_query_manager(
        filters=f'|> filter(fn:(r) => r._measurement == "api_call") \
        |> filter(fn: (r) => r["_field"] == "request_count") \
        |> filter(fn: (r) => r["organisation_id"] == "{organisation_id}")',
        drop_columns='"organisation", "project", "project_id"',
        extra="|> sum()",
        date_range=date_range,
    )

    total = 0
    for table in result:
        for record in table.records:
            total += record.get_value()

    return total


def get_event_list_for_organisation(organisation_id: int):
    """
    Query influx db for usage for given organisation id

    :param organisation_id: an id of the organisation to get usage for

    :return: a number of request counts for organisation in chart.js scheme
    """
    results = InfluxDBWrapper.influx_query_manager(
        filters=f'|> filter(fn:(r) => r._measurement == "api_call") \
                  |> filter(fn: (r) => r["organisation_id"] == "{organisation_id}")',
        drop_columns='"organisation", "organisation_id", "type", "project", "project_id"',
        extra="|> aggregateWindow(every: 24h, fn: sum)",
    )
    dataset = defaultdict(list)
    labels = []
    for result in results:
        for record in result.records:
            dataset[record["resource"]].append(record["_value"])
            if len(labels) != 31:
                labels.append(record.values["_time"].strftime("%Y-%m-%d"))
    return dataset, labels


def get_multiple_event_list_for_organisation(organisation_id: int):
    """
    Query influx db for usage for given organisation id

    :param organisation_id: an id of the organisation to get usage for

    :return: a number of requests for flags, traits, identities
    """
    results = InfluxDBWrapper.influx_query_manager(
        filters=f'|> filter(fn:(r) => r._measurement == "api_call") \
                  |> filter(fn: (r) => r["organisation_id"] == "{organisation_id}")',
        drop_columns='"organisation", "organisation_id", "type", "project", "project_id"',
        extra="|> aggregateWindow(every: 24h, fn: sum)",
    )
    if not results:
        return results

    dataset = [{} for _ in range(len(results[0].records))]

    for result in results:
        for i, record in enumerate(result.records):
            dataset[i][record.values["resource"].capitalize()] = record.values["_value"]
            dataset[i]["name"] = record.values["_time"].strftime("%Y-%m-%d")
    return dataset


def get_multiple_event_list_for_feature(
    environment_id: int, feature_name: str, period: str = "30d"
) -> typing.List[dict]:
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
    :param period: the influx time period to filter on, e.g. 30d, 7d, etc.

    :return: a list of dicts with feature and request count in a specific environment
    """

    results = InfluxDBWrapper.influx_query_manager(
        filters=f'|> filter(fn:(r) => r._measurement == "feature_evaluation") \
                  |> filter(fn: (r) => r["_field"] == "request_count") \
                  |> filter(fn: (r) => r["environment_id"] == "{environment_id}") \
                  |> filter(fn: (r) => r["feature_id"] == "{feature_name}")',
        drop_columns='"organisation", "organisation_id", "type", "project", "project_id"',
        extra=f'|> aggregateWindow(every: {period}, fn: sum, createEmpty: false) \
                   |> yield(name: "sum")',
    )
    if not results:
        return []

    dataset = [{} for _ in range(len(results[0].records))]

    # Iterating over Influx data looking for feature_id, and adding proper requests value and datetime to it
    # todo move it to marshmallow schema
    for result in results:
        for i, record in enumerate(result.records):
            dataset[i][record.values["feature_id"]] = record.values["_value"]
            dataset[i]["datetime"] = record.values["_time"].strftime("%Y-%m-%d")

    return dataset


def get_top_organisations(date_range: str, limit: str = ""):
    """
    Query influx db top used organisations

    :param date_range: data range for top organisations
    :param limit: limit for query


    :return: top organisations in descending order based on api calls.
    """
    if limit:
        limit = f"|> limit(n:{limit})"

    bucket = range_bucket_mappings[date_range]
    results = InfluxDBWrapper.influx_query_manager(
        date_range=date_range,
        bucket=bucket,
        filters='|> filter(fn:(r) => r._measurement == "api_call") \
                    |> filter(fn: (r) => r["_field"] == "request_count")',
        drop_columns='"_start", "_stop", "_time"',
        extra=f'|> group(columns: ["organisation"]) \
              |> sum() \
              |> group() \
              |> sort(columns: ["_value"], desc: true) '
        + limit,
    )

    dataset = {}
    for result in results:
        for record in result.records:
            org_id = int(record.values["organisation"].partition("-")[0])
            dataset[org_id] = record.get_value()
    return dataset


def init_client(url: str, token: str, influx_org: str, influx_bucket: str):
    global influxdb_client, influx, org, bucket, range_bucket_mappings, read_bucket
    influxdb_client = InfluxDBClient(url=url, token=token, org=influx_org)
    org = influx_org
    bucket = influx_bucket
    range_bucket_mappings = {
        "24h": influx_bucket + "_downsampled_15m",
        "7d": influx_bucket + "_downsampled_15m",
        "30d": influx_bucket + "_downsampled_1h",
    }
    read_bucket = influx_bucket + "_downsampled_15m"

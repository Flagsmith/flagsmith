from collections import defaultdict

from django.conf import settings
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

url = settings.INFLUXDB_URL
token = settings.INFLUXDB_TOKEN
influx_org = settings.INFLUXDB_ORG
read_bucket = settings.INFLUXDB_BUCKET + "_downsampled_15m"

influxdb_client = InfluxDBClient(url=url, token=token, org=influx_org)


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
        self.write_api.write(bucket=settings.INFLUXDB_BUCKET, record=self.records)

    @staticmethod
    def influx_query_manager(
        date_range: str = "30d",
        date_stop: str = "now()",
        drop_columns: str = "'organisation', 'organisation_id', 'type', 'project', 'project_id'",
        filters: str = "|> filter(fn:(r) => r._measurement == 'api_call')",
        extra: str = "",
    ):
        query_api = influxdb_client.query_api()

        query = (
            f'from(bucket:"{read_bucket}")'
            f" |> range(start: -{date_range}, stop: {date_stop})"
            f" {filters}"
            f" |> drop(columns: [{drop_columns}])"
            f"{extra}"
        )

        result = query_api.query(org=influx_org, query=query)
        return result


def get_events_for_organisation(organisation_id):
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

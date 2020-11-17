from django.conf import settings
from influxdb_client import InfluxDBClient
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS

url = settings.INFLUXDB_URL
token = settings.INFLUXDB_TOKEN
influx_org = settings.INFLUXDB_ORG
read_bucket = settings.INFLUXDB_BUCKET + "_downsampled_15m"

influxdb_client = InfluxDBClient(
    url=url,
    token=token,
    org=influx_org
)


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


def get_events_for_organisation(organisation_id):
    """
    Query influx db for usage for given organisation id

    :param organisation_id: an id of the organisation to get usage for
    :return: a number of request counts for organisation
    """
    query_api = influxdb_client.query_api()
    query = ' from(bucket:"%s") \
                |> range(start: -30d, stop: now()) \
                |> filter(fn:(r) => r._measurement == "api_call") \
                |> filter(fn: (r) => r["_field"] == "request_count") \
                |> filter(fn: (r) => r["organisation_id"] == "%s") \
                |> drop(columns: ["organisation", "resource",  "project", "project_id"]) \
                |> sum()' % (read_bucket, organisation_id)

    # we should get only one record back
    # just in case iterate over and sum them up
    result = query_api.query(org=influx_org, query=query)
    total = 0
    for table in result:
        for record in table.records:
            total += record.get_value()

    return total

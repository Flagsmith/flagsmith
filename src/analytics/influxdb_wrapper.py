from django.conf import settings
from influxdb_client import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client import InfluxDBClient


influxdb_client = InfluxDBClient(
    url=settings.INFLUXDB_URL,
    token=settings.INFLUXDB_TOKEN,
    org=settings.INFLUXDB_ORG
)


class InfluxDBWrapper:
    def __init__(self, name, field_name, field_value, tags=None):
        self.name = name
        self.point = Point(name)

        tags = tags or {}
        self.record = self._record(field_name, field_value, tags)

        self.write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

    def _record(self, field_name, field_value, tags):
        for tag_key, tag_value in tags.items():
            self.point = self.point.tag(tag_key, tag_value)
        return self.point.field(field_name, field_value)

    def write(self):
        self.write_api.write(bucket=settings.INFLUXDB_BUCKET, record=self.record)

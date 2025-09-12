import argparse
from datetime import datetime

from django.conf import settings
from django.core.management import BaseCommand
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


class Command(BaseCommand):
    help = "Send API usage to InfluxDB"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--tag",
            type=str,
            action="append",
            default=None,
            dest="tags",
            required=True,
            help="Tag to send with the record in the format 'key=value'. "
            "Send multiple tags by providing multiple --tag arguments.",
        )
        parser.add_argument(
            "--bucket",
            type=str,
            dest="bucket_name",
            required=True,
            help="Influx bucket name to write to",
        )

        parser.add_argument(
            "--influx-url",
            type=str,
            default=None,
            dest="influx_url",
            required=False,
            help="Influx API url to use. Defaults to settings.INFLUXDB_URL.",
        )
        parser.add_argument(
            "--influx-token",
            type=str,
            default=None,
            dest="influx_token",
            required=False,
            help="Influx API token to use. Defaults to settings.INFLUXDB_TOKEN.",
        )
        parser.add_argument(
            "--influx-org",
            type=str,
            default=None,
            dest="influx_org",
            required=False,
            help="Influx organisation to use. Defaults to settings.INFLUXDB_ORG.",
        )
        parser.add_argument(
            "--request-count",
            type=int,
            dest="request_count",
            required=False,
            default=1,
            help="Count of requests to send with the data point. Defaults to 1.",
        )
        parser.add_argument(
            "--time",
            type=datetime.fromisoformat,
            required=False,
            default=None,
            dest="time",
            help="Time to send the data point with. Defaults to current time.",
        )

    def handle(  # type: ignore[no-untyped-def]
        self,
        *args,
        tags: list[str],
        bucket_name: str,
        influx_url: str,
        influx_token: str,
        influx_org: str,
        request_count: int,
        time: datetime,
        **kwargs,
    ) -> None:
        influxdb_client = InfluxDBClient(
            url=influx_url or settings.INFLUXDB_URL,
            token=influx_token or settings.INFLUXDB_TOKEN,
            org=influx_org or settings.INFLUXDB_ORG,
            timeout=3000,
        )

        record = (
            Point("api_call")
            .field("request_count", request_count)
            .time(time or datetime.now())
        )

        for tag in tags:
            k, v = tag.split("=")
            record.tag(k, v)

        write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=bucket_name, record=record)

        self.stdout.write(self.style.SUCCESS("Successfully sent data to InfluxDB"))

from django.conf import settings

from .analytics.influxdb_wrapper import (
    InfluxDBWrapper,
    get_event_list_for_organisation,
    get_events_for_organisation,
    get_multiple_event_list_for_feature,
    get_multiple_event_list_for_organisation,
    get_top_organisations,
    init_client,
)

init_client(
    url=settings.INFLUXDB_URL,
    token=settings.INFLUXDB_TOKEN,
    influx_org=settings.INFLUXDB_ORG,
    influx_bucket=settings.INFLUXDB_BUCKET,
)

import logging
from datetime import timedelta

import requests
from app_analytics.influxdb_wrapper import influxdb_client
from django.conf import settings
from influxdb_client import Point, WriteOptions

from environments.models import Environment
from projects.models import Project
from sse import sse_service
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

from .exceptions import SSEAuthTokenNotSet

logger = logging.getLogger(__name__)


@register_task_handler()
def send_environment_update_message_for_project(
    project_id: int,
):
    project = Project.objects.get(id=project_id)

    for environment in project.environments.all():
        send_environment_update_message(
            environment.api_key, environment.updated_at.isoformat()
        )


@register_task_handler()
def send_environment_update_message(environment_key: str, updated_at):
    url = f"{settings.SSE_SERVER_BASE_URL}/sse/environments/{environment_key}/queue-change"
    payload = {"updated_at": updated_at}
    response = requests.post(url, headers=get_auth_header(), json=payload, timeout=2)
    response.raise_for_status()


if settings.AWS_SSE_LOGS_BUCKET_NAME:

    @register_recurring_task(
        run_every=timedelta(minutes=5),
    )
    def update_sse_usage():
        agg_request_count: dict[str, int] = {}
        agg_last_event_generated_at: dict[str, str] = {}

        for log in sse_service.stream_access_logs():
            agg_request_count[log.api_key] = agg_request_count.get(log.api_key, 0) + 1
            agg_last_event_generated_at[log.api_key] = log.generated_at

        with influxdb_client.write_api(
            write_options=WriteOptions(batch_size=100, flush_interval=1000)
        ) as write_api:
            environments = Environment.objects.filter(
                api_key__in=agg_request_count.keys()
            ).values("api_key", "id", "project_id", "project__organisation_id")

            for environment in environments:
                record = _get_influx_point(
                    environment["id"],
                    environment["project_id"],
                    environment["project__organisation_id"],
                    agg_request_count[environment["api_key"]],
                    agg_last_event_generated_at[environment["api_key"]],
                )
                write_api.write(bucket=settings.SSE_INFLUXDB_BUCKET, record=record)


def _get_influx_point(
    environment_id: int, project_id: int, organisation_id: int, count: int, time: str
) -> Point:
    return (
        Point("sse_call")
        .field("request_count", count)
        .tag("organisation_id", organisation_id)
        .tag("project_id", project_id)
        .tag("environment_id", environment_id)
        .time(time)
    )


def get_auth_header():
    if not settings.SSE_AUTHENTICATION_TOKEN:
        raise SSEAuthTokenNotSet()

    return {"Authorization": f"Token {settings.SSE_AUTHENTICATION_TOKEN}"}

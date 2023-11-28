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
        run_every=timedelta(seconds=60),
    )
    def update_sse_usage():
        with influxdb_client.write_api(
            write_options=WriteOptions(batch_size=1000, flush_interval=2000)
        ) as write_api:
            for log in sse_service.stream_access_logs():
                environment = Environment.get_from_cache(log.api_key)

                if not environment:
                    logger.warning("Invalid  api_key %s", log.api_key)
                    continue

                record = _get_influx_point(environment, log.generated_at)
                write_api.write(bucket=settings.SSE_INFLUXDB_BUCKET, record=record)


def _get_influx_point(environment: Environment, event_time: str) -> Point:
    return (
        Point("sse_call")
        .field("request_count", 1)
        .tag("organisation_id", environment.project.organisation_id)
        .tag("project_id", environment.project_id)
        .tag("environment_id", environment.id)
        .time(event_time)
    )


def get_auth_header():
    if not settings.SSE_AUTHENTICATION_TOKEN:
        raise SSEAuthTokenNotSet()

    return {"Authorization": f"Token {settings.SSE_AUTHENTICATION_TOKEN}"}

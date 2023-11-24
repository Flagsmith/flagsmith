import csv
import logging
from io import StringIO

import boto3
import gnupg
import requests
from app_analytics.influxdb_wrapper import influxdb_client
from django.conf import settings
from influxdb_client import Point, WriteOptions

from environments.models import Environment
from projects.models import Project
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

from .exceptions import SSEAuthTokenNotSet

s3 = boto3.resource("s3")
gpg = gnupg.GPG()

bucket = s3.Bucket(settings.FASTLY_LOGS_AWS_BUCKET_NAME)

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


@register_recurring_task(
    run_every=60,
)
def track_usage():
    data = []
    for log_file in bucket.objects.all():
        encrypted_body = log_file.get()["Body"].read()
        print(log_file.key)
        decrypted_body = gpg.decrypt(encrypted_body)
        print(decrypted_body)

        reader = csv.reader(StringIO(decrypted_body.data.decode()), delimiter=",")
        with influxdb_client.write_api(
            write_options=WriteOptions(batch_size=1000, flush_interval=2000)
        ) as write_api:
            for row in reader:
                data.append({"time": row[0], "key": row[1].strip()})
                api_key = row[1].strip()
                envent_time = row[0]
                environment = Environment.get_from_cache(api_key)

                if not environment:
                    logger.warning("Invalid  api_key %s", api_key)
                    continue
                event = influx_point(environment, envent_time)
                write_api.write(bucket=settings.INFLUXDB_BUCKET, record=event)


def influx_point(environment: Environment, event_time) -> Point:
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

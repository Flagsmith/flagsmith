import csv
import logging
from functools import wraps
from io import StringIO
from typing import Generator

import boto3
import gnupg
from django.conf import settings

from sse import tasks
from sse.dataclasses import SSEAccessLogs

logger = logging.getLogger(__name__)

GNUPG_HOME = "/app/.gnupg"


def _sse_enabled(get_project_from_first_arg=lambda obj: obj.project):
    """
    Decorator that only call the service function if sse is enabled else return None.
    i.e: settings are configured and the project has sse enabled.

    :param get_project_from_first_arg: function that takes the first argument
        of the decorated function and returns the project object.
    """

    def decorator(service_func):
        @wraps(service_func)
        def wrapper(*args, **kwargs):
            project = get_project_from_first_arg(args[0])
            if all(
                [
                    settings.SSE_SERVER_BASE_URL,
                    settings.SSE_AUTHENTICATION_TOKEN,
                    project.enable_realtime_updates,
                ]
            ):
                return service_func(*args, **kwargs)
            return None

        return wrapper

    return decorator


@_sse_enabled(get_project_from_first_arg=lambda obj: obj)
def send_environment_update_message_for_project(project):
    tasks.send_environment_update_message_for_project.delay(args=(project.id,))


@_sse_enabled()
def send_environment_update_message_for_environment(environment):
    tasks.send_environment_update_message.delay(
        args=(environment.api_key, environment.updated_at.isoformat())
    )


def stream_access_logs() -> Generator[SSEAccessLogs, None, None]:
    gpg = gnupg.GPG(gnupghome=GNUPG_HOME)
    bucket = boto3.resource("s3").Bucket(settings.AWS_SSE_LOGS_BUCKET_NAME)

    for log_file in bucket.objects.all():
        encrypted_body = log_file.get()["Body"].read()
        decrypted_body = gpg.decrypt(encrypted_body)

        reader = csv.reader(StringIO(decrypted_body.data.decode()))

        for row in reader:
            try:
                log = SSEAccessLogs(*row)
            except TypeError:
                logger.warning("Invalid row in SSE access log file: %s", row)
                continue
            yield log

        log_file.delete()

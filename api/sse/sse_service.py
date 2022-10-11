# from functools import wraps
from typing import List

from django.conf import settings

from . import tasks

# def call_function_if(condition: callable[[Any], bool]):
#     def decorator(f):
#         @wraps(f)
#         def wrapper(*args, **kwargs):
#             if condition(*args, **kwargs):
#                 return f(*args, **kwargs)
#             return f(*args, **kwargs)

#         return wrapper

#     return decorator


# def sse_enabled_required(f):
#     @wraps(f)
#     def wrapper(*args, **kwargs):
#         if all([settings.SSE_SERVER_BASE_URL, settings.SSE_AUTHENTICATION_TOKEN]):
#             return
#         return f(*args, **kwargs)

#     return wrapper


# @sse_enabled_required
def send_environment_update_message_using_project(project):
    if not should_send_message_to_sse(project):
        return

    environment_keys = list(
        project.environments.all().values_list("api_key", flat=True)
    )
    tasks.send_environment_update_messages.delay(args=(environment_keys,))


# @sse_enabled_required
def send_environment_update_message_using_environment(environment):
    if not should_send_message_to_sse(environment.project):
        return

    tasks.send_environment_update_message.delay(args=(environment.api_key,))


# @sse_enabled_required
def send_identity_update_message(environment, identifier: str):
    if not should_send_message_to_sse(environment.project):
        return
    tasks.send_identity_update_message.delay(args=(environment.api_key, identifier))


# @sse_enabled_required
def send_identity_update_messages(environment, identifiers: List[str]):
    if not should_send_message_to_sse(environment.project):
        return

    tasks.send_identity_update_messages.delay(
        args=(
            environment.api_key,
            identifiers,
        )
    )


def should_send_message_to_sse(project):
    return all(
        [
            settings.SSE_SERVER_BASE_URL,
            settings.SSE_AUTHENTICATION_TOKEN,
            project.enable_realtime_updates,
        ]
    )

import logging
import uuid

import requests
from app_analytics.influxdb_wrapper import InfluxDBWrapper
from django.conf import settings
from django.core.cache import caches
from six.moves.urllib.parse import quote  # type: ignore[import-untyped]  # python 2/3 compatible urllib import
from task_processor.decorators import register_task_handler  # type: ignore[import-untyped]

from environments.models import Environment
from util.util import postpone

logger = logging.getLogger(__name__)

environment_cache = caches[settings.ENVIRONMENT_CACHE_NAME]

GOOGLE_ANALYTICS_BASE_URL = "https://www.google-analytics.com"
GOOGLE_ANALYTICS_COLLECT_URL = GOOGLE_ANALYTICS_BASE_URL + "/collect"
GOOGLE_ANALYTICS_BATCH_URL = GOOGLE_ANALYTICS_BASE_URL + "/batch"
DEFAULT_DATA = "v=1&tid=" + settings.GOOGLE_ANALYTICS_KEY

# dictionary of resources to their corresponding actions
# when tracking events in GA / Influx
TRACKED_RESOURCE_ACTIONS = {
    "flags": "flags",
    "identities": "identity_flags",
    "traits": "traits",
    "environment-document": "environment_document",
}


@postpone
def track_request_googleanalytics_async(request):  # type: ignore[no-untyped-def]
    return track_request_googleanalytics(request)  # type: ignore[no-untyped-call]


@postpone
def track_request_influxdb_async(request):  # type: ignore[no-untyped-def]
    return track_request_influxdb(request)  # type: ignore[no-untyped-call]


def get_resource_from_uri(request_uri):  # type: ignore[no-untyped-def]
    """
    Split the uri so we can determine the resource that is being requested
    (note that because it starts with a /, the first item in the list will be a blank string)

    :param request: (HttpRequest) the request being made
    """
    split_uri = request_uri.split("/")[1:]
    if not (len(split_uri) >= 3 and split_uri[0] == "api"):
        logger.debug("not tracking event for uri %s" % request_uri)
        # this isn't an API request so we don't need to track an event for it
        return None

    # uri will be in the form /api/v1/<resource>/...
    return split_uri[2]


def track_request_googleanalytics(request):  # type: ignore[no-untyped-def]
    """
    Utility function to track a request to the API with the specified URI

    :param request: (HttpRequest) the request being made
    """
    pageview_data = DEFAULT_DATA + "t=pageview&dp=" + quote(request.path, safe="")
    # send pageview request
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=pageview_data)

    resource = get_resource_from_uri(request.path)  # type: ignore[no-untyped-call]

    if resource in TRACKED_RESOURCE_ACTIONS:
        environment = Environment.get_from_cache(  # type: ignore[no-untyped-call]
            request.headers.get("X-Environment-Key")
        )
        if environment is None:
            return

        track_event(environment.project.organisation.get_unique_slug(), resource)  # type: ignore[no-untyped-call]


def track_event(category, action, label="", value=""):  # type: ignore[no-untyped-def]
    data = (
        DEFAULT_DATA
        + "&t=event"
        + "&ec="
        + category
        + "&ea="
        + action
        + "&cid="
        + str(uuid.uuid4())
    )
    data = data + "&el=" + label if label else data
    data = data + "&ev=" + value if value else data
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=data)


def track_request_influxdb(request):  # type: ignore[no-untyped-def]
    """
    Sends API event data to InfluxDB

    :param request: (HttpRequest) the request being made
    """
    resource = get_resource_from_uri(request.path)  # type: ignore[no-untyped-call]

    if resource and resource in TRACKED_RESOURCE_ACTIONS:
        environment = Environment.get_from_cache(  # type: ignore[no-untyped-call]
            request.headers.get("X-Environment-Key")
        )
        if environment is None:
            return

        tags = {
            "resource": resource,
            "organisation": environment.project.organisation.get_unique_slug(),
            "organisation_id": environment.project.organisation_id,
            "project": environment.project.name,
            "project_id": environment.project_id,
            "environment": environment.name,
            "environment_id": environment.id,
            "host": request.get_host(),
        }

        influxdb = InfluxDBWrapper("api_call")  # type: ignore[no-untyped-call]
        influxdb.add_data_point("request_count", 1, tags=tags)  # type: ignore[no-untyped-call]
        influxdb.write()  # type: ignore[no-untyped-call]


@register_task_handler()  # type: ignore[misc]
def track_feature_evaluation_influxdb(
    environment_id: int, feature_evaluations: dict[str, int]
) -> None:
    """
    Sends Feature analytics event data to InfluxDB

    :param environment_id: (int) the id of the environment the feature is being evaluated within
    :param feature_evaluations: (dict) A collection of key id / evaluation counts
    """
    influxdb = InfluxDBWrapper("feature_evaluation")  # type: ignore[no-untyped-call]

    for feature_name, evaluation_count in feature_evaluations.items():
        tags = {"feature_id": feature_name, "environment_id": environment_id}
        influxdb.add_data_point("request_count", evaluation_count, tags=tags)  # type: ignore[no-untyped-call]

    influxdb.write()  # type: ignore[no-untyped-call]


@register_task_handler()  # type: ignore[misc]
def track_feature_evaluation_influxdb_v2(
    environment_id: int, feature_evaluations: list[dict[str, int | str | bool]]
) -> None:
    """
    Sends Feature analytics event data to InfluxDB

    :param environment_id: (int) the id of the environment the feature is being evaluated within
    :param feature_evaluations: (list) A collection of feature evaluations including feature name / evaluation counts.
    """
    influxdb = InfluxDBWrapper("feature_evaluation")  # type: ignore[no-untyped-call]

    for feature_evaluation in feature_evaluations:
        feature_name = feature_evaluation["feature_name"]
        evaluation_count = feature_evaluation["count"]

        # Note that "feature_id" is a misnamed as it's actually to
        # the name of the feature. This was to match existing behavior.
        tags = {"feature_id": feature_name, "environment_id": environment_id}
        influxdb.add_data_point("request_count", evaluation_count, tags=tags)  # type: ignore[no-untyped-call]

    influxdb.write()  # type: ignore[no-untyped-call]

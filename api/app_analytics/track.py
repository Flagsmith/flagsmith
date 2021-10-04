import logging
import uuid

import requests
from app_analytics.influxdb_wrapper import InfluxDBWrapper
from django.conf import settings
from django.core.cache import caches
from six.moves.urllib.parse import quote  # python 2/3 compatible urllib import

from environments.models import Environment
from util.util import postpone

logger = logging.getLogger(__name__)

environment_cache = caches[settings.ENVIRONMENT_CACHE_LOCATION]

GOOGLE_ANALYTICS_BASE_URL = "https://www.google-analytics.com"
GOOGLE_ANALYTICS_COLLECT_URL = GOOGLE_ANALYTICS_BASE_URL + "/collect"
GOOGLE_ANALYTICS_BATCH_URL = GOOGLE_ANALYTICS_BASE_URL + "/batch"
DEFAULT_DATA = "v=1&tid=" + settings.GOOGLE_ANALYTICS_KEY

# dictionary of resources to their corresponding actions when tracking events in GA
TRACKED_RESOURCE_ACTIONS = {
    "flags": "flags",
    "identities": "identity_flags",
    "traits": "traits",
}


@postpone
def track_request_googleanalytics_async(request):
    return track_request_googleanalytics(request)


@postpone
def track_request_influxdb_async(request, influxdb):
    return track_request_influxdb(request, influxdb)


def get_influxdb_wrapper():
    return InfluxDBWrapper("api_call")


def get_resource_from_uri(request_uri):
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


def track_request_googleanalytics(request):
    """
    Utility function to track a request to the API with the specified URI

    :param request: (HttpRequest) the request being made
    """
    pageview_data = DEFAULT_DATA + "t=pageview&dp=" + quote(request.path, safe="")
    # send pageview request
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=pageview_data)

    resource = get_resource_from_uri(request.path)

    if resource in TRACKED_RESOURCE_ACTIONS:
        environment = Environment.get_from_cache(
            request.headers.get("X-Environment-Key")
        )
        if environment is None:
            return

        track_event(environment.project.organisation.get_unique_slug(), resource)


def track_event(category, action, label="", value=""):
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


def track_request_influxdb(request, influxdb):
    """
    Sends API event data to InfluxDB

    :param request: (HttpRequest) the request being made
    """
    resource = get_resource_from_uri(request.path)

    if resource and resource in TRACKED_RESOURCE_ACTIONS:
        environment = Environment.get_from_cache(
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
        }

        # influxdb = InfluxDBWrapper("api_call")
        influxdb.add_data_point("request_count", 1, tags=tags)
        influxdb.write()


def track_feature_evaluation_influxdb(environment_id, feature_evaluations):
    """
    Sends Feature analytics event data to InfluxDB

    :param environment_id: (int) the id of the environment the feature is being evaluated within
    :param feature_evaluations: (dict) A collection of key id / evaluation counts
    """
    influxdb = InfluxDBWrapper("feature_evaluation")

    for feature_id, evaluation_count in feature_evaluations.items():
        tags = {"feature_id": feature_id, "environment_id": environment_id}
        influxdb.add_data_point("request_count", evaluation_count, tags=tags)

    influxdb.write()

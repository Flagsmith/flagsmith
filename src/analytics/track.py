import logging
import uuid
from threading import Thread

import requests, json
from django.conf import settings
from django.core.cache import caches
from six.moves.urllib.parse import quote  # python 2/3 compatible urllib import

from analytics.influxdb_wrapper import InfluxDBWrapper
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
    "traits": "traits"
}


@postpone
def track_request_googleanalytics_async(request):
    return track_request_googleanalytics(request)

@postpone
def track_request_influxdb_async(request):
    return track_request_influxdb(request)

@postpone
def track_request_amplitude_async(environment, identity, all_feature_states):
    return track_request_amplitude(environment, identity, all_feature_states)

@postpone
def track_event_datadog_async(organisation, data, event_type):
    return track_event_datadog(organisation, data, event_type)

def get_resource_from_uri(request_uri):
    """
    Split the uri so we can determine the resource that is being requested
    (note that because it starts with a /, the first item in the list will be a blank string)

    :param request: (HttpRequest) the request being made
    """
    split_uri = request_uri.split('/')[1:]
    if not (len(split_uri) >= 3 and split_uri[0] == 'api'):
        logger.debug('not tracking event for uri %s' % request_uri)
        # this isn't an API request so we don't need to track an event for it
        return None

    # uri will be in the form /api/v1/<resource>/...
    return split_uri[2]


def track_request_googleanalytics(request):
    """
    Utility function to track a request to the API with the specified URI

    :param request: (HttpRequest) the request being made
    """
    pageview_data = DEFAULT_DATA + "t=pageview&dp=" + quote(request.path, safe='')
    # send pageview request
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=pageview_data)

    resource = get_resource_from_uri(request.path)

    if resource in TRACKED_RESOURCE_ACTIONS:
        environment = Environment.get_from_cache(request.headers.get('X-Environment-Key'))
        track_event(environment.project.organisation.get_unique_slug(), resource)


def track_event(category, action, label='', value=''):
    data = DEFAULT_DATA + "&t=event" + \
           "&ec=" + category + \
           "&ea=" + action + "&cid=" + str(uuid.uuid4())
    data = data + "&el=" + label if label else data
    data = data + "&ev=" + value if value else data
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=data)


def track_request_influxdb(request):
    """
    Sends API event data to InfluxDB

    :param request: (HttpRequest) the request being made
    """
    resource = get_resource_from_uri(request.path)

    if resource and resource in TRACKED_RESOURCE_ACTIONS:
        environment = Environment.get_from_cache(request.headers.get('X-Environment-Key'))

        tags = {
            "resource": resource,
            "organisation": environment.project.organisation.get_unique_slug(),
            "organisation_id": environment.project.organisation_id,
            "project": environment.project.name,
            "project_id": environment.project_id
        }

        influxdb = InfluxDBWrapper("api_call", "request_count", 1, tags=tags)
        influxdb.write()


def track_request_amplitude(environment, identity, all_feature_states):
    """
    Sends Identity flags to Amplitude for AB testing
    """
    identification = {}
    identification["user_id"] = identity.identifier

    user_properties = {}
    for feature_state in all_feature_states:
        user_properties[str(feature_state.feature.name)] = feature_state.get_feature_state_value()     
    identification["user_properties"] = user_properties

    data = {
        "api_key": environment.amplitude_api_key,
        "identification": json.dumps([identification])
    }
    response = requests.post(f"https://api.amplitude.com/identify", data=data)


def track_event_datadog(organisation, data, event_type):
    """
    Sends Audit events to Datadog
    """
    event = {}
    event["text"] = "this is a test"
    event["title"] = "this is a title test"
    
    response = requests.post(
        organisation.datadog_api_base_url + "api/v1/events?api_key=" + organisation.datadog_api_key, 
        data=json.dumps(event))
    print(str(response))
import uuid

from django.core.cache import caches
from six.moves.urllib.parse import quote  # python 2/3 compatible urllib import
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import requests

from threading import Thread
from django.conf import settings

from environments.models import Environment

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

influxdb_client = InfluxDBClient(url=settings.INFLUXDB_URL, token=settings.INFLUXDB_TOKEN, org=settings.INFLUXDB_ORG)


def postpone(function):
    def decorator(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator


@postpone
def track_request_googleanalytics_async(request):
    return track_request_googleanalytics(request)


@postpone
def track_request_influxdb_async(request):
    return track_request_influxdb(request)


def track_request_googleanalytics(request):
    """
    Utility function to track a request to the API with the specified URI

    :param request: (HttpRequest) the request being made
    """
    uri = request.path
    data = DEFAULT_DATA + "t=pageview&dp=" + quote(uri, safe='')
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=data)

    resource = get_resource_from_uri(request)
    if resource is not None:
        environment = Environment.get_from_cache(request.headers.get('X-Environment-Key'))
        track_event(environment.project.organisation.get_unique_slug(), resource)


def get_resource_from_uri(request):
    uri = request.path
    resource = uri.split('/')[3]  # uri will be in the form /api/v1/<resource>/...
    return TRACKED_RESOURCE_ACTIONS[resource]


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
    """
    environment = Environment.get_from_cache(request.headers.get('X-Environment-Key'))

    point = Point("api_call") \
        .tag("resource", get_resource_from_uri(request)) \
        .tag("organisation", environment.project.organisation.get_unique_slug()) \
        .tag("organisation_id", environment.project.organisation_id) \
        .tag("project", environment.project.name) \
        .tag("project_id", environment.project_id) \
        .field("request_count", 1)

    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    write_api.write(bucket="api_prod", record=point)

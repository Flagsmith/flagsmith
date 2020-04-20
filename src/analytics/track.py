import uuid

from django.core.cache import caches
from six.moves.urllib.parse import quote  # python 2/3 compatible urllib import
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


def postpone(function):
    def decorator(*args, **kwargs):
        t = Thread(target=function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator


@postpone
def track_request_async(request):
    return track_request(request)


def track_request(request):
    """
    Utility function to track a request to the API with the specified URI

    :param request: (HttpRequest) the request being made
    """
    uri = request.path
    data = DEFAULT_DATA + "t=pageview&dp=" + quote(uri, safe='')
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=data)

    resource = uri.split('/')[3]  # uri will be in the form /api/v1/<resource>/...
    if resource in TRACKED_RESOURCE_ACTIONS:
        environment = Environment.get_from_cache(request.headers.get('X-Environment-Key'))
        track_event(environment.project.organisation.get_unique_slug(), TRACKED_RESOURCE_ACTIONS[resource])


def track_event(category, action, label='', value=''):
    data = DEFAULT_DATA + "&t=event" + \
        "&ec=" + category + \
        "&ea=" + action + "&cid=" + str(uuid.uuid4())
    data = data + "&el=" + label if label else data
    data = data + "&ev=" + value if value else data
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=data)

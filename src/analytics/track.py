import uuid

from six.moves.urllib.parse import quote  # python 2/3 compatible urllib import
import requests

from threading import Thread
from django.conf import settings

GOOGLE_ANALYTICS_BASE_URL = "https://www.google-analytics.com"
GOOGLE_ANALYTICS_COLLECT_URL = GOOGLE_ANALYTICS_BASE_URL + "/collect"
GOOGLE_ANALYTICS_BATCH_URL = GOOGLE_ANALYTICS_BASE_URL + "/batch"
DEFAULT_DATA = "v=1&tid=" + settings.GOOGLE_ANALYTICS_KEY


def postpone(function):
    def decorator(*args, **kwargs):
        t = Thread(target = function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator


@postpone
def post_async(url, data):
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=data)


def track_request(uri):
    """
    Utility function to track a request to the API with the specified URI

    :param uri: (string) the request URI
    """
    data = DEFAULT_DATA + "t=pageview&dp=" + quote(uri, safe='')
    post_async(GOOGLE_ANALYTICS_COLLECT_URL, data=data)


def track_event(category, action, label='', value=''):
    data = DEFAULT_DATA + "&t=event" + \
        "&ec=" + category + \
        "&ea=" + action + "&cid=" + str(uuid.uuid4())
    data = data + "&el=" + label if label else data
    data = data + "&ev=" + value if value else data
    post_async(GOOGLE_ANALYTICS_COLLECT_URL, data=data)

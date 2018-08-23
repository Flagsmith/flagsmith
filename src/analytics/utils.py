import urllib
import requests

from django.conf import settings

GOOGLE_ANALYTICS_BASE_URL = "https://www.google-analytics.com"
GOOGLE_ANALYTICS_COLLECT_URL = GOOGLE_ANALYTICS_BASE_URL + "/collect"
GOOGLE_ANALYTICS_BATCH_URL = GOOGLE_ANALYTICS_BASE_URL + "/batch"
DEFAULT_DATA = "v=1&tid=" + settings.GOOGLE_ANALYTICS_KEY + "&cid=555&"


def track_request(uri):
    """
    Utility function to track a request to the API with the specified URI

    :param uri: (string) the request URI
    """
    data = DEFAULT_DATA + "t=pageview&dp=" + urllib.quote(uri, safe='')
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=data)


def track_event(category, action, label='', value=''):
    data = DEFAULT_DATA + "t=event" + \
           "&ec=" + category + \
           "&ea=" + action + \
           "&el=" + label + \
           "&ev=" + value
    requests.post(GOOGLE_ANALYTICS_COLLECT_URL, data=data)


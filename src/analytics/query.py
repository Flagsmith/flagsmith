import json

from apiclient.discovery import build
from django.conf import settings
from google.oauth2 import service_account

GA_SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
GA_API_NAME = 'analytics'
GA_API_VERSION = 'v3'


def get_service():
    """
    Get the google service object to use to query the API
    """
    credentials = service_account.Credentials.from_service_account_info(
        json.loads(settings.GOOGLE_SERVICE_ACCOUNT), scopes=GA_SCOPES)

    # Build the service object.
    return build(GA_API_NAME, GA_API_VERSION, credentials=credentials)


def get_events_for_organisation(organisation):    
    """
    Get number of tracked events for last 30 days for an organisation

    :return: number of events as integer
    """
    try:
        ga_response = get_service().data().ga().get(
            ids=settings.GA_TABLE_ID,
            start_date='30daysAgo',
            end_date='today',
            metrics='ga:totalEvents',
            dimensions='ga:date',
            filters=f'ga:eventCategory=={organisation.get_unique_slug()}').execute()
        return int(ga_response['totalsForAllResults']['ga:totalEvents'])
    except:
        return 0

import json

from apiclient.discovery import build  # type: ignore[import-untyped]
from django.conf import settings
from google.oauth2 import service_account

GA_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]
GA_API_NAME = "analytics"
GA_API_VERSION = "v3"


def get_service():  # type: ignore[no-untyped-def]
    """
    Get the google service object to use to query the API
    """
    credentials = service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
        json.loads(settings.GOOGLE_SERVICE_ACCOUNT),  # type: ignore[arg-type]
        scopes=GA_SCOPES,
    )

    # Build the service object.
    return build(GA_API_NAME, GA_API_VERSION, credentials=credentials)


def get_events_for_organisation(organisation):  # type: ignore[no-untyped-def]
    """
    Get number of tracked events for last 30 days for an organisation

    :return: number of events as integer
    """
    ga_response = (
        get_service()  # type: ignore[no-untyped-call]
        .data()
        .ga()
        .get(
            ids=settings.GA_TABLE_ID,
            start_date="30daysAgo",
            end_date="today",
            metrics="ga:totalEvents",
            dimensions="ga:date",
            filters=f"ga:eventCategory=={organisation.get_unique_slug()}",
        )
        .execute()
    )

    return int(ga_response["totalsForAllResults"]["ga:totalEvents"])

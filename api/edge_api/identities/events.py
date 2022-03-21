import json

import boto3
from django.conf import settings

events_client = None
if settings.IDENTITY_MIGRATION_EVENT_BUS:
    events_client = boto3.client("events")


def send_migration_event(project_id: int):
    event = {
        "EventBusName": settings.IDENTITY_MIGRATION_EVENT_BUS,
        "Source": "flagsmith.api.migrate",
        "DetailType": "Migrate Identities to dynamodb",
        "Detail": json.dumps({"project_id": project_id}),
    }

    events_client.put_events(Entries=[event])

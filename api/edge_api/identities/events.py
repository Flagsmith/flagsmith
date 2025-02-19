import json

import boto3
from django.conf import settings

events_client = None
if settings.IDENTITY_MIGRATION_EVENT_BUS_NAME:
    events_client = boto3.client("events")


def send_migration_event(project_id: int):  # type: ignore[no-untyped-def]
    event = {
        "EventBusName": settings.IDENTITY_MIGRATION_EVENT_BUS_NAME,
        "Source": "flagsmith.api.migrate",
        "DetailType": "Migrate Identities to dynamodb",
        "Detail": json.dumps({"project_id": project_id}),
    }

    events_client.put_events(Entries=[event])  # type: ignore[union-attr]

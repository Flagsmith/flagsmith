import json
import logging

import requests

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from features.models import Feature
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper
from segments.models import Segment

logger = logging.getLogger(__name__)

EVENTS_API_URI = "api/v2/events/ingest"


class DynatraceWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(self, base_url: str, api_key: str, entity_selector: str):
        self.base_url = base_url
        self.api_key = api_key
        self.entity_selector = entity_selector
        self.url = f"{self.base_url}{EVENTS_API_URI}?api-token={self.api_key}"

    def _track_event(self, event: dict) -> None:
        event["entitySelector"] = self.entity_selector
        response = requests.post(
            self.url, headers=self._headers(), data=json.dumps(event)
        )
        logger.debug(
            "Sent event to Dynatrace. Response code was %s" % response.status_code
        )

    def _headers(self) -> dict:
        return {"Content-Type": "application/json"}

    @staticmethod
    def generate_event_data(audit_log_record: AuditLog) -> dict:
        log = audit_log_record.log
        environment_name = audit_log_record.environment_name
        email = audit_log_record.author_identifier

        flag_properties = {
            "event": f"{log} by user {email}",
            "environment": environment_name,
            "dt.event.deployment.name": _get_deployment_name(audit_log_record),
        }

        return {
            "title": "Flagsmith flag change.",
            "eventType": "CUSTOM_DEPLOYMENT",
            "properties": flag_properties,
        }


def _get_deployment_name(audit_log_record: AuditLog) -> str:
    if audit_log_record.related_object_type == RelatedObjectType.FEATURE.name:
        if feature := (
            Feature.objects.all_with_deleted()
            .filter(id=audit_log_record.related_object_id)
            .first()
        ):
            return f"Flagsmith Deployment - Flag Changed: {feature.name}"
    elif audit_log_record.related_object_type == RelatedObjectType.FEATURE_STATE.name:
        if feature := (
            Feature.objects.all_with_deleted()
            .filter(feature_states__id=audit_log_record.related_object_id)
            .distinct()
            .first()
        ):
            return f"Flagsmith Deployment - Flag Changed: {feature.name}"
    elif audit_log_record.related_object_type == RelatedObjectType.SEGMENT.name:
        if (
            segment := Segment.objects.all_with_deleted()
            .filter(id=audit_log_record.related_object_id)
            .first()
        ):
            return f"Flagsmith Deployment - Segment Changed: {segment.name}"

    # use 'Deployment' as a fallback to maintain current behaviour in
    # the event of an issue with new functionality
    return "Deployment"

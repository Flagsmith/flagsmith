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

# use 'Deployment' as a fallback to maintain current behaviour in the
# event that we cannot determine the correct name to return.
DEFAULT_DEPLOYMENT_NAME = "Deployment"


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
    related_object_type = RelatedObjectType[audit_log_record.related_object_type]

    if related_object_type in (
        RelatedObjectType.FEATURE,
        RelatedObjectType.FEATURE_STATE,
    ):
        return _get_deployment_name_for_feature(
            audit_log_record.related_object_id, related_object_type
        )
    elif related_object_type == RelatedObjectType.SEGMENT:
        return _get_deployment_name_for_segment(audit_log_record.related_object_id)

    # use 'Deployment' as a fallback to maintain current behaviour in the
    # event that we cannot determine the correct name to return.
    return DEFAULT_DEPLOYMENT_NAME


def _get_deployment_name_for_feature(
    object_id: int, object_type: RelatedObjectType
) -> str:
    qs = Feature.objects.all_with_deleted()
    if object_type == RelatedObjectType.FEATURE:
        qs = qs.filter(id=object_id)
    elif object_type == RelatedObjectType.FEATURE_STATE:
        qs = qs.filter(feature_states__id=object_id).distinct()

    if feature := qs.first():
        return f"Flagsmith Deployment - Flag Changed: {feature.name}"

    # use 'Deployment' as a fallback to maintain current behaviour in the
    # event that we cannot determine the correct name to return.
    return DEFAULT_DEPLOYMENT_NAME


def _get_deployment_name_for_segment(object_id: int) -> str:
    if segment := Segment.objects.all_with_deleted().filter(id=object_id).first():
        return f"Flagsmith Deployment - Segment Changed: {segment.name}"

    return DEFAULT_DEPLOYMENT_NAME

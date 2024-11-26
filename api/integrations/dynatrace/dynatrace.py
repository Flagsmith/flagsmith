import json
import logging

import requests

from audit.models import AuditLog
from audit.services import get_audited_instance_from_audit_log_record
from features.models import Feature, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
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
    audited_instance = get_audited_instance_from_audit_log_record(audit_log_record)

    if isinstance(audited_instance, Feature):
        deployment_name = _get_deployment_name_for_feature(audited_instance)
    elif isinstance(audited_instance, FeatureState) or isinstance(
        audited_instance, EnvironmentFeatureVersion
    ):
        deployment_name = _get_deployment_name_for_feature(audited_instance.feature)
    elif isinstance(audited_instance, Segment):
        deployment_name = _get_deployment_name_for_segment(audited_instance)
    else:
        # use 'Deployment' as a fallback to maintain current behaviour in the
        # event that we cannot determine the correct name to return.
        deployment_name = DEFAULT_DEPLOYMENT_NAME

    return deployment_name


def _get_deployment_name_for_feature(feature: Feature) -> str:
    return f"Flagsmith Deployment - Flag Changed: {feature.name}"


def _get_deployment_name_for_segment(segment: Segment) -> str:
    return f"Flagsmith Deployment - Segment Changed: {segment.name}"

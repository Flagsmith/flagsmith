import json
import logging
from enum import Enum
from typing import Any, List, Union

import requests
from django.core.serializers import serialize

from external_resources.models import ExternalResources
from integrations.github.models import GithubConfiguration
from webhooks.webhooks import WebhookEventType

logger = logging.getLogger(__name__)

BASE_URL = "https://4376-131-0-197-145.ngrok-free.app/api/flagsmith-webhook"


class GithubResourceType(Enum):
    GITHUB_ISSUE = "Github Issue"
    GITHUB_PR = "Github PR"


class GithubWrapper:
    def __init__(
        self,
        configuration: GithubConfiguration,
        session: Union[requests.Session, None] = None,
    ) -> None:
        self.flagsmith_github_app_url = BASE_URL

        self.configuration = configuration
        self.session = session or requests.Session()

    def track_event(
        self,
        event: dict[str, Any],
        event_type: WebhookEventType,
        external_resources: List[ExternalResources],
    ) -> None:
        projects = serialize("json", self.configuration.repository_config.all())
        data = {
            "event_type": event_type.value,
            "data": event,
            "installation_id": self.configuration.installation_id,
            "organisation_id": self.configuration.installation_id,
            "projects": json.loads(projects),
            "external_resources": external_resources,
        }
        response = self.session.post(
            f"{self.flagsmith_github_app_url}", data=json.dumps(data)
        )
        print("DEBUG: Sent event to GitHub. Response code was:", response)
        logger.debug(
            "Sent event to GitHub. Response code was %s" % response.status_code
        )

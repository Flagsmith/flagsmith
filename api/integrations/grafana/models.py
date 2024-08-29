"""
Example `integration_data` entry:

```
    "grafana": {
        "perEnvironment": false,
        "image": "/static/images/integrations/grafana.svg",
        "docs": "https://docs.flagsmith.com/integrations/apm/grafana",
        "fields": [
            {
                "key": "base_url",
                "label": "Base URL",
                "default": "https://grafana.com"
            },
            {
                "key": "api_key",
                "label": "Service account token",
                "hidden": true
            }
        ],
        "tags": [
            "logging"
        ],
        "title": "Grafana",
        "description": "Receive Flagsmith annotations to your Grafana instance on feature flag and segment changes."
    },
```
"""

import logging

from django.db import models

from integrations.common.models import IntegrationsModel
from organisations.models import Organisation
from projects.models import Project

logger = logging.getLogger(__name__)


class GrafanaProjectConfiguration(IntegrationsModel):
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="grafana_config"
    )


class GrafanaOrganisationConfiguration(IntegrationsModel):
    organisation = models.OneToOneField(
        Organisation, on_delete=models.CASCADE, related_name="grafana_config"
    )

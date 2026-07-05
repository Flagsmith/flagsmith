from django.db import models

from integrations.common.models import IntegrationHealthRecord


def record_integration_health(
    integration_config: models.Model,
    status_code: int,
) -> None:
    IntegrationHealthRecord.objects.create(
        content_object=integration_config,
        status_code=status_code,
    )

import logging
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction

from integrations.common.models import IntegrationHealthRecord

logger = logging.getLogger(__name__)


def record_integration_health(
    integration_config: models.Model,
    status_code: int,
) -> None:
    try:
        with transaction.atomic():
            IntegrationHealthRecord.objects.create(
                content_object=integration_config,
                status_code=status_code,
            )
    except Exception:
        logger.exception("Failed to record integration health.")


def get_latest_integration_health(
    integration_config: models.Model,
) -> dict[str, Any] | None:
    latest_record = (
        IntegrationHealthRecord.objects.filter(
            content_type=ContentType.objects.get_for_model(integration_config),
            object_id=integration_config.pk,
        )
        .order_by("-created_at")
        .first()
    )

    if not latest_record:
        return None

    return {
        "status_code": latest_record.status_code,
        "is_healthy": 200 <= latest_record.status_code < 300,
        "created_at": latest_record.created_at,
    }

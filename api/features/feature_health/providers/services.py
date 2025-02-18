import uuid

import structlog
from django.core import signing
from django.urls import reverse

from features.feature_health.models import FeatureHealthProvider

logger = structlog.get_logger("feature_health")

_provider_webhook_signer = signing.Signer(sep="/", salt="feature_health")


def get_webhook_path_from_provider(
    provider: FeatureHealthProvider,
) -> str:
    webhook_path = _provider_webhook_signer.sign_object(
        provider.uuid.hex,
    )
    return reverse(
        "api-v1:feature-health-webhook",
        args=[webhook_path],
    )


def get_provider_from_webhook_path(path: str) -> FeatureHealthProvider | None:
    try:
        hex_string = _provider_webhook_signer.unsign_object(path)
    except signing.BadSignature:
        logger.warning("invalid-feature-health-webhook-path-requested", path=path)
        return None
    feature_health_provider_uuid = uuid.UUID(hex_string)
    return FeatureHealthProvider.objects.filter(
        uuid=feature_health_provider_uuid
    ).first()

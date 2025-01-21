import typing
import uuid

import structlog
from django.core import signing

from environments.models import Environment
from features.feature_health.constants import (
    FEATURE_HEALTH_WEBHOOK_PATH_PREFIX,
    UNHEALTHY_TAG_COLOUR,
)
from features.feature_health.models import (
    FeatureHealthEvent,
    FeatureHealthEventType,
    FeatureHealthProvider,
    FeatureHealthProviderType,
)
from features.feature_health.providers import sample
from projects.tags.models import Tag, TagType

if typing.TYPE_CHECKING:
    from features.feature_health.types import FeatureHealthProviderResponse
    from features.models import Feature

logger = structlog.get_logger("feature_health")

_provider_webhook_signer = signing.Signer(sep="/", salt="feature_health")


def get_webhook_path_from_provider(
    provider: FeatureHealthProvider,
) -> str:
    return FEATURE_HEALTH_WEBHOOK_PATH_PREFIX + _provider_webhook_signer.sign_object(
        provider.uuid.hex,
    )


def get_provider_from_webhook_path(path: str) -> FeatureHealthProvider | None:
    try:
        hex_string = _provider_webhook_signer.unsign_object(path)
    except signing.BadSignature:
        logger.warning("invalid-webhook-path-requested", path=path)
        return None
    feature_health_provider_uuid = uuid.UUID(hex_string)
    return FeatureHealthProvider.objects.filter(
        uuid=feature_health_provider_uuid
    ).first()


def get_provider_response(
    provider: FeatureHealthProvider, payload: str
) -> "FeatureHealthProviderResponse | None":
    if provider.type == FeatureHealthProviderType.SAMPLE:
        return sample.map_payload_to_provider_response(payload)
    logger.error(
        "invalid-provider-type-requested",
        provider_type=provider.type,
        provider_id=provider.uuid,
    )
    return None


def create_feature_health_event_from_webhook(
    path: str,
    payload: str,
) -> FeatureHealthEvent | None:
    if provider := get_provider_from_webhook_path(path):
        if response := get_provider_response(provider, payload):
            project = provider.project
            if feature := Feature.objects.filter(
                project=provider.project, name=response.feature_name
            ).first():
                if response.environment_name:
                    environment = Environment.objects.filter(
                        project=project, name=response.environment_name
                    ).first()
                else:
                    environment = None
                return FeatureHealthEvent.objects.create(
                    feature=feature,
                    environment=environment,
                    type=response.event_type,
                    provider_name=provider.name,
                    reason=response.reason,
                )
    return None


def update_feature_unhealthy_tag(feature: "Feature") -> None:
    if feature_health_event := FeatureHealthEvent.objects.get_latest_by_feature(
        feature
    ):
        unhealthy_tag, _ = Tag.objects.get_or_create(
            name="Unhealthy",
            project=feature.project,
            defaults={"color": UNHEALTHY_TAG_COLOUR},
            is_system_tag=True,
            type=TagType.UNHEALTHY,
        )
        if feature_health_event.type == FeatureHealthEventType.UNHEALTHY:
            feature.tags.add(unhealthy_tag)
        else:
            feature.tags.remove(unhealthy_tag)
        feature.save()

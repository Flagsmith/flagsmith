import json
import typing

import structlog

from api_keys.user import APIKeyUser
from environments.models import Environment
from features.feature_health.constants import (
    FEATURE_HEALTH_EVENT_MANUALLY_DISMISSED_MESSAGE,
    UNHEALTHY_TAG_COLOUR,
    UNHEALTHY_TAG_LABEL,
)
from features.feature_health.mappers import (
    map_feature_health_event_data_to_feature_health_event,
)
from features.feature_health.models import (
    FeatureHealthEvent,
    FeatureHealthEventType,
    FeatureHealthProvider,
    FeatureHealthProviderName,
)
from features.feature_health.providers import grafana, webhook
from features.feature_health.types import FeatureHealthEventReason
from features.models import Feature
from projects.tags.models import Tag, TagType
from users.models import FFAdminUser

if typing.TYPE_CHECKING:
    from features.feature_health.types import FeatureHealthProviderResponse

logger = structlog.get_logger("feature_health")


PROVIDER_RESPONSE_GETTERS: dict[
    str,
    typing.Callable[[str], "FeatureHealthProviderResponse"],
] = {
    FeatureHealthProviderName.GRAFANA.value: grafana.get_provider_response,
    FeatureHealthProviderName.WEBHOOK.value: webhook.get_provider_response,
}


def get_provider_response(
    provider: FeatureHealthProvider, payload: str
) -> "FeatureHealthProviderResponse | None":
    response = None
    try:
        response = PROVIDER_RESPONSE_GETTERS[provider.name](payload)
    except (KeyError, ValueError) as exc:
        logger.error(
            "feature-health-provider-error",
            provider_name=provider.name,
            provider_id=provider.uuid,
            exc_info=exc,
        )
    return response


def create_feature_health_events_from_provider(
    provider: FeatureHealthProvider,
    payload: str,
) -> list[FeatureHealthEvent]:
    from features.feature_health import tasks

    response = get_provider_response(provider, payload)
    project = provider.project
    events_to_create = []
    feature_ids_to_update = set()
    if response:
        for event_data in response.events:
            if feature := Feature.objects.filter(
                project=provider.project, name=event_data.feature_name
            ).first():
                feature_ids_to_update.add(feature.id)
                if environment_name := event_data.environment_name:
                    environment = Environment.objects.filter(
                        project=project,
                        name=environment_name,
                    ).first()
                else:
                    environment = None
                events_to_create.append(
                    map_feature_health_event_data_to_feature_health_event(
                        feature_health_event_data=event_data,
                        feature=feature,
                        environment=environment,
                    )
                )
    FeatureHealthEvent.objects.bulk_create(events_to_create)
    for feature_id in feature_ids_to_update:
        tasks.update_feature_unhealthy_tag.delay(args=(feature_id,))
    return events_to_create


def update_feature_unhealthy_tag(feature: "Feature") -> None:
    if feature_health_events := [
        *FeatureHealthEvent.objects.get_latest_by_feature(feature)
    ]:
        unhealthy_tag, _ = Tag.objects.get_or_create(
            label=UNHEALTHY_TAG_LABEL,
            project=feature.project,
            defaults={"color": UNHEALTHY_TAG_COLOUR},
            is_system_tag=True,
            type=TagType.UNHEALTHY,
        )
        if any(
            FeatureHealthEventType(feature_health_event.type)
            == FeatureHealthEventType.UNHEALTHY
            for feature_health_event in feature_health_events
        ):
            feature.tags.add(unhealthy_tag)
        else:
            feature.tags.remove(unhealthy_tag)
        feature.save()


def dismiss_feature_health_event(
    feature_health_event: FeatureHealthEvent,
    dismissed_by: FFAdminUser | APIKeyUser,
) -> None:
    from features.feature_health import tasks

    if (
        FeatureHealthEventType(feature_health_event.type)
        != FeatureHealthEventType.UNHEALTHY
    ):
        logger.warning(
            "feature-health-event-dismissal-not-supported",
            feature_health_event_id=feature_health_event.id,
            feature_health_event_external_id=feature_health_event.external_id,
            feature_health_event_type=feature_health_event.type,
            provider_name=feature_health_event.provider_name,
        )
        return

    reason: FeatureHealthEventReason = {
        "text_blocks": [
            {
                "text": FEATURE_HEALTH_EVENT_MANUALLY_DISMISSED_MESSAGE % dismissed_by,
            }
        ],
        "url_blocks": [],
    }

    FeatureHealthEvent.objects.create(
        feature=feature_health_event.feature,
        environment=feature_health_event.environment,
        type=FeatureHealthEventType.HEALTHY.value,
        reason=json.dumps(reason),
        provider_name=feature_health_event.provider_name,
        external_id=feature_health_event.external_id,
    )

    tasks.update_feature_unhealthy_tag.delay(
        args=(feature_health_event.feature.id,),
    )

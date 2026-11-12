import json
import typing

import pydantic
import structlog

from api_keys.user import APIKeyUser
from environments.models import Environment
from features.feature_health.constants import (
    FEATURE_HEALTH_EVENT_MANUALLY_DISMISSED_MESSAGE,
    UNHEALTHY_TAG_COLOUR,
    UNHEALTHY_TAG_LABEL,
)
from features.feature_health.exceptions import (
    FeatureHealthEventsNotCreatedError,
    FeatureHealthWebhookPayloadInvalidError,
)
from features.feature_health.mappers import (
    map_feature_health_event_data_to_feature_health_event,
    map_validation_error_to_payload_error_details,
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
    from projects.models import Project

logger = structlog.get_logger("feature_health")


PROVIDER_RESPONSE_GETTERS: dict[
    str,
    typing.Callable[[str], "FeatureHealthProviderResponse"],
] = {
    FeatureHealthProviderName.GRAFANA.value: grafana.get_provider_response,
    FeatureHealthProviderName.WEBHOOK.value: webhook.get_provider_response,
}

PROVIDER_ENVIRONMENT_NAMES_GETTERS: dict[
    str,
    typing.Callable[[str], list[str]],
] = {
    FeatureHealthProviderName.GRAFANA.value: grafana.map_payload_to_environment_names,
    FeatureHealthProviderName.WEBHOOK.value: webhook.map_payload_to_environment_names,
}


def get_provider_response(
    provider: FeatureHealthProvider, payload: str
) -> "FeatureHealthProviderResponse | None":
    response = None
    try:
        response = PROVIDER_RESPONSE_GETTERS[provider.name](payload)
    except pydantic.ValidationError as exc:
        errors = map_validation_error_to_payload_error_details(exc)
        log = logger.bind(
            organisation__id=provider.project.organisation_id,
            project__id=provider.project_id,
            provider__id=provider.uuid,
            provider__name=provider.name,
        )
        if environment_id := _get_environment_id(
            provider.project,
            PROVIDER_ENVIRONMENT_NAMES_GETTERS[provider.name](payload),
        ):
            log = log.bind(environment__id=environment_id)
        log.warning(
            "webhook_payload.invalid",
            errors=_summarise_payload_error_details(errors),
        )
        raise FeatureHealthWebhookPayloadInvalidError(errors) from exc
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
    """
    Create feature health events from a provider's webhook payload.

    Raise `FeatureHealthWebhookPayloadInvalidError` if the payload is invalid,
    and `FeatureHealthEventsNotCreatedError` if it yields no events.
    """
    from features.feature_health import tasks

    if not (response := get_provider_response(provider, payload)):
        raise FeatureHealthEventsNotCreatedError()

    project = provider.project
    events_to_create = []
    feature_ids_to_update = set()
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

    if not events_to_create:
        feature_names = sorted({event.feature_name for event in response.events})
        if feature_names:
            detail = (
                "No feature health events were created: feature(s) "
                f"{', '.join(map(repr, feature_names))} not found in the project."
            )
        else:
            detail = (
                "No feature health events were created: "
                "the payload does not reference any feature."
            )
        log = logger.bind(
            organisation__id=project.organisation_id,
            project__id=project.id,
            provider__id=provider.uuid,
            provider__name=provider.name,
        )
        if environment_id := _get_environment_id(
            project,
            [event.environment_name for event in response.events],
        ):
            log = log.bind(environment__id=environment_id)
        log.info(
            "webhook_payload.no_events_created",
            feature_names=feature_names,
        )
        raise FeatureHealthEventsNotCreatedError(detail)

    FeatureHealthEvent.objects.bulk_create(events_to_create)
    for feature_id in feature_ids_to_update:
        tasks.update_feature_unhealthy_tag.delay(args=(feature_id,))
    return events_to_create


def _summarise_payload_error_details(
    errors: list[dict[str, str]],
) -> str:
    return "; ".join(
        f"{error['loc']}: {error['msg']}" if error["loc"] else error["msg"]
        for error in errors
    )


def _get_environment_id(
    project: "Project",
    environment_names: typing.Iterable[str | None],
) -> int | None:
    # Only attribute an event to an environment when it's unambiguous.
    if len(unique_names := {name for name in environment_names if name}) != 1:
        return None
    environment_id: int | None = (
        Environment.objects.filter(project=project, name=unique_names.pop())
        .values_list("id", flat=True)
        .first()
    )
    return environment_id


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

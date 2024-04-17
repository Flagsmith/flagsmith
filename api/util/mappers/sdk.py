from typing import TYPE_CHECKING, TypeAlias

from util.mappers.engine import (
    map_environment_to_engine,
    map_identity_to_engine,
)

if TYPE_CHECKING:  # pragma: no cover
    from environments.identities.models import Identity
    from environments.models import Environment

ENVIRONMENT_RESPONSE_EXCLUDE_FIELDS = [
    "amplitude_config",
    "dynatrace_config",
    "heap_config",
    "mixpanel_config",
    "rudderstack_config",
    "segment_config",
    "webhook_config",
]


SDKDocumentValue: TypeAlias = dict[str, "SDKDocumentValue"] | str | bool | None | float
SDKDocument: TypeAlias = dict[str, SDKDocumentValue]


def map_environment_to_sdk_document(
    environment: "Environment",
    *,
    identities_with_overrides: list["Identity"] | None = None,
) -> SDKDocument:
    """
    Map an `environments.models.Environment` instance to an SDK document
    used by SDKs with local evaluation mode.

    It's virtually the same data that gets indexed in DynamoDB,
    except it presents identity overrides and omits integrations configurations.
    """
    # Get the engine data.
    engine_environment = map_environment_to_engine(environment, with_integrations=False)

    # No reading from ORM past this point!

    # Prepare relationships.
    engine_environment.identity_overrides = [
        map_identity_to_engine(identity) for identity in identities_with_overrides or []
    ]

    return engine_environment.model_dump(
        exclude=ENVIRONMENT_RESPONSE_EXCLUDE_FIELDS,
    )

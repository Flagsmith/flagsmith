from typing import TYPE_CHECKING, TypeAlias

from environments.constants import IDENTITY_INTEGRATIONS_RELATION_NAMES
from util.mappers.engine import (
    map_environment_to_engine,
    map_identity_to_engine,
)

if TYPE_CHECKING:  # pragma: no cover
    from environments.models import Environment


SDKDocumentValue: TypeAlias = dict[str, "SDKDocumentValue"] | str | bool | None | float
SDKDocument: TypeAlias = dict[str, SDKDocumentValue]

SDK_DOCUMENT_EXCLUDE = [
    *IDENTITY_INTEGRATIONS_RELATION_NAMES,
    "dynatrace_config",
]


def map_environment_to_sdk_document(environment: "Environment") -> SDKDocument:
    """
    Map an `environments.models.Environment` instance to an SDK document
    used by SDKs with local evaluation mode.

    It's virtually the same data that gets indexed in DynamoDB,
    except it presents identity overrides and omits integrations configurations.
    """
    # Read relationships.
    identities_with_overrides = {}
    for feature_state in environment.feature_states.all():
        if (identity_id := feature_state.identity_id) and (
            identity_id not in identities_with_overrides
        ):
            identities_with_overrides[identity_id] = feature_state.identity

    # Get the engine data.
    engine_environment = map_environment_to_engine(environment, with_integrations=False)

    # No reading from ORM past this point!

    # Prepare relationships.
    engine_environment.identity_overrides = [
        map_identity_to_engine(identity, with_traits=False)
        for identity in identities_with_overrides.values()
    ]

    return engine_environment.model_dump(
        exclude=SDK_DOCUMENT_EXCLUDE,
    )

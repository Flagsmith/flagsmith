from typing import TYPE_CHECKING

from django.db.models import Q
from flag_engine.engine import get_evaluation_result

from environments.identities.mappers import map_identity_to_evaluation_context
from environments.identities.types import IdentityEvaluation

if TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from environments.models import Environment


def evaluate_identity(
    identity: "Identity",
    *,
    traits: "list[Trait] | None" = None,
    feature_name: str | None = None,
    additional_filters: Q | None = None,
) -> IdentityEvaluation:
    """Evaluate every flag in `identity`'s environment for that identity."""
    context, feature_states_by_id = map_identity_to_evaluation_context(
        identity,
        traits=traits,
        feature_name=feature_name,
        additional_filters=additional_filters,
    )
    return IdentityEvaluation(get_evaluation_result(context), feature_states_by_id)


def replace_identity_environment(
    identity: "Identity",
    environment: "Environment",
) -> None:
    """
    Replace the environment relation on an identity model instance.

    Used for optimisation on SDK request paths, where identities are fetched
    without joining the environment: assigning the relation keeps
    `identity.environment` accesses from querying the database, and an
    environment instance sourced from the environment cache already carries
    its related project, organisation, and integration configurations.
    """
    identity.environment = environment

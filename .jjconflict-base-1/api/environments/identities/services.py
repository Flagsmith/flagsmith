from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.models import Environment


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

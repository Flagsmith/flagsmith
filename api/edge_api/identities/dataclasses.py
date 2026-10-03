from dataclasses import dataclass
from enum import Enum


class OrphanedIdentityOverrideReason(Enum):
    """
    Why an `environments_v2` identity override no longer reflects its identity.
    """

    # No identity document exists for the identifier any more.
    IDENTITY_DELETED = "identity_deleted"
    # The identifier exists, but as a different identity than the one the
    # override was written against, so the override can never be reached.
    IDENTITY_UUID_CHANGED = "identity_uuid_changed"
    # The identity is the same one, but no longer overrides this feature.
    OVERRIDE_REMOVED = "override_removed"


@dataclass(frozen=True)
class OrphanedIdentityOverride:
    document_key: str
    identifier: str
    identity_uuid: str
    feature_id: int
    feature_name: str
    reason: OrphanedIdentityOverrideReason

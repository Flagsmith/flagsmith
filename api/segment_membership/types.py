from datetime import datetime
from typing import Any, TypedDict

# (environment_key, identifier, identity_key, traits, inserted_at)
ClickHouseIdentityRow = tuple[str, str, str, dict[str, object] | None, datetime]

# (identifier, identity_key, traits)
ClickHouseReadIdentityRow = tuple[str, str, dict[str, object] | None]


class SegmentMember(TypedDict):
    identifier: str
    identity_key: str
    traits: dict[str, Any] | None

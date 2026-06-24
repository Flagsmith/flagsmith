from typing import Any, TypedDict

# (environment_key, identifier, identity_key, traits)
ClickHouseIdentityRow = tuple[str, str, str, dict[str, object] | None]

# (identifier, identity_key, traits)
ClickHouseReadIdentityRow = tuple[str, str, dict[str, object] | None]


class SegmentMember(TypedDict):
    identifier: str
    identity_key: str
    traits: dict[str, Any] | None

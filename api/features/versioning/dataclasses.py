import typing
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, computed_field

if typing.TYPE_CHECKING:
    from api_keys.models import MasterAPIKey
    from users.models import FFAdminUser


class Conflict(BaseModel):
    segment_id: int | None = None
    original_cr_id: int | None = None
    published_at: datetime | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_environment_default(self) -> bool:
        return self.segment_id is None


@dataclass
class FlagChangeSet:
    enabled: bool
    feature_state_value: typing.Any
    type_: str

    user: typing.Optional["FFAdminUser"] = None
    api_key: typing.Optional["MasterAPIKey"] = None

    segment_id: int | None = None
    segment_priority: int | None = None


@dataclass
class SegmentOverrideChangeSet:
    """Represents a single segment override change."""

    segment_id: int
    enabled: bool
    feature_state_value: typing.Any
    type_: str
    priority: int | None = None


@dataclass
class FlagChangeSetV2:
    """Represents V2 feature state changes (environment default + segment overrides)."""

    # Environment default state
    environment_default_enabled: bool
    environment_default_value: typing.Any
    environment_default_type: str

    # Segment overrides (list)
    segment_overrides: list[SegmentOverrideChangeSet]

    # Audit fields
    user: typing.Optional["FFAdminUser"] = None
    api_key: typing.Optional["MasterAPIKey"] = None

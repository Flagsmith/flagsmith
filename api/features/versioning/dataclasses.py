from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, computed_field

from features.feature_states.models import FeatureValueType

if TYPE_CHECKING:
    from rest_framework.request import Request

    from api_keys.models import MasterAPIKey
    from users.models import FFAdminUser


@dataclass
class AuthorData:
    user: FFAdminUser | None = None
    api_key: MasterAPIKey | None = None

    @classmethod
    def from_request(cls, request: Request) -> AuthorData:
        from users.models import FFAdminUser

        if type(request.user) is FFAdminUser:
            return cls(user=request.user)
        elif hasattr(request.user, "key"):
            return cls(api_key=request.user.key)
        else:
            raise ValueError("Request user must be FFAdminUser or have an API key")


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
    author: AuthorData
    enabled: bool
    feature_state_value: str
    type_: FeatureValueType

    segment_id: int | None = None
    segment_priority: int | None = None


@dataclass
class SegmentOverrideChangeSet:
    segment_id: int
    enabled: bool
    feature_state_value: str
    type_: FeatureValueType
    priority: int | None = None


@dataclass
class FlagChangeSetV2:
    author: AuthorData
    environment_default_enabled: bool
    environment_default_value: str
    environment_default_type: FeatureValueType

    segment_overrides: list[SegmentOverrideChangeSet] = field(default_factory=list)

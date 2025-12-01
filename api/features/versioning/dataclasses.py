from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, computed_field

if TYPE_CHECKING:
    from rest_framework.request import Request

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
class AuditFieldsMixin:
    user: FFAdminUser | None = field(default=None, kw_only=True)
    api_key: str | None = field(default=None, kw_only=True)

    def set_audit_fields_from_request(self, request: Request) -> None:
        from users.models import FFAdminUser

        if type(request.user) is FFAdminUser:
            self.user = request.user
        elif hasattr(request.user, "key"):
            self.api_key = request.user.key
        else:
            raise ValueError("Request user must be FFAdminUser or have an API key")


@dataclass
class FlagChangeSet(AuditFieldsMixin):
    enabled: bool
    feature_state_value: str
    type_: str

    segment_id: int | None = None
    segment_priority: int | None = None


@dataclass
class SegmentOverrideChangeSet:
    segment_id: int
    enabled: bool
    feature_state_value: str
    type_: str
    priority: int | None = None


@dataclass
class FlagChangeSetV2(AuditFieldsMixin):
    environment_default_enabled: bool
    environment_default_value: str
    environment_default_type: str

    segment_overrides: list[SegmentOverrideChangeSet] = field(default_factory=list)

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
    feature_state_value: str
    type_: str

    user: typing.Optional["FFAdminUser"] = None
    api_key: typing.Optional["MasterAPIKey"] = None

    segment_id: str | None = None

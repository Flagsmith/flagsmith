from datetime import datetime

from pydantic import BaseModel, computed_field


class Conflict(BaseModel):
    segment_id: int | None = None
    original_cr_id: int | None = None
    published_at: datetime | None = None

    @computed_field
    @property
    def is_environment_default(self) -> bool:
        return self.segment_id is None

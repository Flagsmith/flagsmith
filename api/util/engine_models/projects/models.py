import typing

from pydantic import BaseModel, Field

from util.engine_models.organisations.models import OrganisationModel
from util.engine_models.segments.models import SegmentModel


class ProjectModel(BaseModel):
    id: int
    name: str
    organisation: OrganisationModel
    hide_disabled_flags: bool = False
    segments: typing.List[SegmentModel] = Field(default_factory=list)
    enable_realtime_updates: bool = False
    server_key_only_feature_ids: typing.List[int] = Field(default_factory=list)

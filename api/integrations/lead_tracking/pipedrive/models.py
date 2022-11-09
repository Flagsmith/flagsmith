import datetime
import typing
from abc import ABC
from dataclasses import dataclass, field

from marshmallow.schema import Schema

from integrations.lead_tracking.pipedrive.schemas import (
    PipedriveLeadRequestSchema,
    PipedriveLeadResponseSchema,
    PipedriveOrganizationRequestSchema,
    PipedriveOrganizationResponseSchema,
    PipedriveValueSchema,
)


class BasePipedriveModel(ABC):
    request_schema: Schema = None
    response_schema: Schema = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_request_data(self) -> dict:
        return self.request_schema.dump(self.__dict__)

    @classmethod
    def from_response_data(cls, data: dict) -> "BasePipedriveModel":
        return cls(**cls.response_schema.load(data))


@dataclass
class PipedriveValue(BasePipedriveModel):
    request_schema = PipedriveValueSchema()
    response_schema = PipedriveValueSchema()

    amount: int
    currency: str


@dataclass
class PipedriveLead(BasePipedriveModel):
    request_schema = PipedriveLeadRequestSchema()
    response_schema = PipedriveLeadResponseSchema()

    title: str
    id: str = None
    owner_id: int = None
    label_ids: typing.List[int] = field(default_factory=list)
    person_id: int = None
    organization_id: int = None
    value: PipedriveValue = None
    expected_close_date: datetime.date = None
    visible_to: int = None
    was_seen: bool = None


@dataclass
class PipedriveOrganization(BasePipedriveModel):
    request_schema = PipedriveOrganizationRequestSchema()
    response_schema = PipedriveOrganizationResponseSchema()

    name: str
    id: int = None

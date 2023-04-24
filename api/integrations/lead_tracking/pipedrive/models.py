import datetime
import typing

from marshmallow.schema import Schema

from integrations.lead_tracking.pipedrive.schemas import (
    BasePipedriveCustomFieldSchema,
    PipedriveLeadLabelSchema,
    PipedriveLeadSchema,
    PipedriveOrganizationSchema,
    PipedrivePersonSchema,
    PipedriveValueSchema,
)


class BasePipedriveModel:
    schema: Schema = None

    @classmethod
    def from_response_data(
        cls, data: dict, schema: Schema = None
    ) -> "BasePipedriveModel":
        schema = schema or cls.schema
        return cls(**schema.load(data))


class PipedriveValue(BasePipedriveModel):
    schema = PipedriveValueSchema()

    def __init__(self, amount: int, currency: str):
        super().__init__()
        self.amount = amount
        self.currency = currency


class PipedriveLead(BasePipedriveModel):
    schema = PipedriveLeadSchema()

    def __init__(
        self,
        title: str,
        id: str = None,
        owner_id: int = None,
        label_ids: typing.List[str] = None,
        person_id: int = None,
        organization_id: int = None,
        value: PipedriveValue = None,
        expected_close_date: datetime.date = None,
        visible_to: int = None,
        was_seen: bool = None,
    ):
        super().__init__()
        self.title = title
        self.id = id
        self.owner_id = owner_id
        self.label_ids = label_ids or []
        self.person_id = person_id
        self.organization_id = organization_id
        self.value = value
        self.expected_close_date = expected_close_date
        self.visible_to = visible_to
        self.was_seen = was_seen


class PipedriveOrganization(BasePipedriveModel):
    schema = PipedriveOrganizationSchema()

    def __init__(
        self,
        name: str,
        id: int = None,
        organization_fields: typing.Dict[str, typing.Any] = None,
    ):
        super().__init__()
        self.name = name
        self.id = id
        self.organization_fields = organization_fields

    @staticmethod
    def get_org_name_from_domain(domain: str) -> str:
        """
        Generate an organisation name from the provided domain.
            e.g. google.com -> google
        """
        parts = domain.split(".")
        if len(parts) < 2:
            raise ValueError(f"Invalid domain: {domain}")
        return parts[-2]


class BasePipedriveCustomField(BasePipedriveModel):
    schema = BasePipedriveCustomFieldSchema()

    def __init__(
        self,
        name: str,
        field_type: str = "varchar",
        key: str = None,
        add_visible_flag: bool = True,
        id: int = None,
    ):
        super().__init__()
        self.name = name
        self.field_type = field_type
        self.key = key
        self.add_visible_flag = add_visible_flag
        self.id = id


class PipedriveOrganizationField(BasePipedriveCustomField):
    pass


class PipedriveDealField(BasePipedriveCustomField):
    pass


class PipedrivePerson(BasePipedriveModel):
    schema = PipedrivePersonSchema()

    def __init__(self, name: str, id: int = None):
        self.name = name
        self.id = id


class PipedriveLeadLabel(BasePipedriveModel):
    schema = PipedriveLeadLabelSchema()

    def __init__(self, id: str, name: str, color: str):
        self.id = id
        self.name = name
        self.color = color

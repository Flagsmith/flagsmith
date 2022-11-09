from marshmallow import EXCLUDE, fields, post_dump
from marshmallow.schema import Schema


class BaseSchema(Schema):
    @post_dump()
    def remove_null_values(self, data: dict, many: bool, **kwargs):
        if many:
            return [{k: v for k, v in d.items() if v is not None} for d in data]
        return {k: v for k, v in data.items() if v is not None}

    class Meta:
        unknown = EXCLUDE


class PipedriveValueSchema(BaseSchema):
    value = fields.Int()
    currency = fields.Str()


class PipedriveLeadRequestSchema(BaseSchema):
    title = fields.Str()
    owner_id = fields.Int()
    label_ids = fields.List(fields.Int)
    person_id = fields.Int(allow_none=True)
    organization_id = fields.Int()
    value = fields.Nested(PipedriveValueSchema, allow_none=True)
    expected_close_date = fields.Date(format="%Y-%m-%d", allow_none=True)
    visible_to = fields.Int()
    was_seen = fields.Bool()


class PipedriveLeadResponseSchema(PipedriveLeadRequestSchema):
    id = fields.UUID()


class PipedriveOrganizationRequestSchema(BaseSchema):
    name = fields.Str()


class PipedriveOrganizationResponseSchema(PipedriveOrganizationRequestSchema):
    id = fields.Int()

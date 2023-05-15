from marshmallow import EXCLUDE, fields
from marshmallow.schema import Schema


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


class PipedriveValueSchema(BaseSchema):
    value = fields.Int()
    currency = fields.Str()


class PipedriveLeadSchema(BaseSchema):
    id = fields.Str()
    title = fields.Str()
    owner_id = fields.Int()
    label_ids = fields.List(fields.Str)
    person_id = fields.Int(allow_none=True)
    organization_id = fields.Int()
    value = fields.Nested(PipedriveValueSchema, allow_none=True)
    expected_close_date = fields.Date(format="%Y-%m-%d", allow_none=True)
    visible_to = fields.Int()
    was_seen = fields.Bool()


class PipedriveOrganizationSchema(BaseSchema):
    id = fields.Int()
    name = fields.Str()


class BasePipedriveCustomFieldSchema(BaseSchema):
    id = fields.Int(allow_none=True)
    key = fields.Str()
    name = fields.Str()
    field_type = fields.Str()
    add_visible_flag = fields.Bool()


class PipedrivePersonSchema(BaseSchema):
    name = fields.Str()
    id = fields.Int()


class PipedriveLeadLabelSchema(BaseSchema):
    id = fields.Str()
    name = fields.Str()
    color = fields.Str()

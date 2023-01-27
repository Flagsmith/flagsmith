from dataclasses import dataclass
from datetime import date

from marshmallow import INCLUDE, Schema, fields, post_load, pre_load


@dataclass
class UsageData:
    day: date
    flags: int = 0
    traits: int = 0
    identities: int = 0
    environment_document: int = 0


@dataclass
class FeatureUsageData:
    day: date
    count: int = 0


class FeatureUsageDataSchema(Schema):
    count = fields.Integer(allow_none=True)
    day = fields.Date(allow_none=True)

    class Meta:
        unknown = INCLUDE

    @pre_load
    def preprocess(self, data, **kwargs):
        valid_data = {"day": data.pop("datetime")}
        valid_data["count"] = data.popitem()[1]
        return valid_data

    @post_load
    def make_usage_data(self, data, **kwargs):
        return FeatureUsageData(**data)


class UsageDataSchema(Schema):
    flags = fields.Integer(data_key="Flags", allow_none=True)
    traits = fields.Integer(data_key="Traits", allow_none=True)
    identities = fields.Integer(data_key="Identities", allow_none=True)
    environment_document = fields.Integer(
        data_key="Environment-document", allow_none=True
    )
    day = fields.Date(data_key="name", allow_none=True)

    class Meta:
        unknown = INCLUDE

    @post_load
    def make_usage_data(self, data, **kwargs):
        return UsageData(**data)

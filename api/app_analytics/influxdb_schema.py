from marshmallow import EXCLUDE, Schema, fields, post_load, pre_load

from .dataclasses import FeatureEvaluationData, UsageData


class FeatureEvaluationDataSchema(Schema):
    count = fields.Integer(allow_none=True)
    day = fields.Date(allow_none=True)

    class Meta:
        unknown = EXCLUDE

    @pre_load
    def preprocess(self, data, **kwargs):  # type: ignore[no-untyped-def]
        # the data returned by influx db looks like this:
        # {
        #     "datetime": "2021-01-01",
        #     "some_feature_name": 10
        # }
        day = data.pop("datetime")
        # Use popitem because we don't know the name of the feature
        # and it's the only item left in the dict
        _, count = data.popitem()
        return {"day": day, "count": count}

    @post_load
    def make_usage_data(self, data, **kwargs):  # type: ignore[no-untyped-def]
        return FeatureEvaluationData(**data)


class UsageDataSchema(Schema):
    flags = fields.Integer(data_key="Flags", allow_none=True)
    traits = fields.Integer(data_key="Traits", allow_none=True)
    identities = fields.Integer(data_key="Identities", allow_none=True)
    environment_document = fields.Integer(
        data_key="Environment-document", allow_none=True
    )
    day = fields.Date(data_key="name", allow_none=True)

    class Meta:
        unknown = EXCLUDE

    @post_load
    def make_usage_data(self, data, **kwargs):  # type: ignore[no-untyped-def]
        return UsageData(**data)

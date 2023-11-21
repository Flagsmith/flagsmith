from typing import Any, List

from marshmallow import Schema, fields

from features.models import FeatureState
from features.versioning.models import EnvironmentFeatureVersion


class _FeatureSchema(Schema):
    id = fields.Int()
    name = fields.Str()


class _UserSchema(Schema):
    id = fields.Int()
    email = fields.Str()


class _FeatureStateSchema(Schema):
    enabled = fields.Bool()
    value = fields.Method(serialize="get_feature_state_value")

    def get_feature_state_value(self, obj: FeatureState) -> Any:
        return obj.get_feature_state_value()


class EnvironmentFeatureVersionWebhookDataSerializer(Schema):
    uuid = fields.UUID()
    feature = fields.Nested(_FeatureSchema())
    published_by = fields.Nested(_UserSchema(), allow_none=True)
    feature_states = fields.Method(serialize="get_feature_states")

    def get_feature_states(self, obj: EnvironmentFeatureVersion) -> List[dict]:
        schema = _FeatureStateSchema()
        return schema.dump([fs for fs in obj.feature_states.all()], many=True)

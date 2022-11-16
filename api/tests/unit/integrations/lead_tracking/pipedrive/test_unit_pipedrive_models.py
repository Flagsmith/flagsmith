from marshmallow import fields
from marshmallow.schema import Schema

from integrations.lead_tracking.pipedrive.models import BasePipedriveModel


def test_base_pipedrive_model_from_api_response():
    # Given
    class MySchema(Schema):
        foo = fields.Str()

    class MyClass(BasePipedriveModel):
        schema = MySchema()

        def __init__(self, foo: str):
            self.foo = foo

    # When
    o = MyClass.from_response_data(data={"foo": "bar"})

    # Then
    assert o.foo == "bar"

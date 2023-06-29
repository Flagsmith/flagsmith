from json import JSONEncoder
from typing import Any, Type

from pydantic.json import pydantic_encoder
from rest_framework.renderers import JSONRenderer


class PydanticJSONEncoder(JSONEncoder):
    def default(self, obj: Any) -> Any:
        return pydantic_encoder(obj)


class PydanticJSONRenderer(JSONRenderer):
    encoder_class: Type[JSONEncoder] = PydanticJSONEncoder

from django.core import exceptions
from django.db import models


class GenericObjectID(models.PositiveIntegerField):
    def value_from_object(self, obj):
        """
        Override to return natural_key of the object instead of pk; used by our custom serializer
        to support import/export of objects with natural keys
        """
        return obj.content_object.natural_key()[0]

    def to_python(self, value):
        """
        Override to allow string values; used by our custom deserializer
        to support import/export using natural keys
        """
        if value is None:
            return value
        if isinstance(value, str):
            return value
        try:
            return int(value)
        except (TypeError, ValueError):
            raise exceptions.ValidationError(
                self.error_messages["invalid"],
                code="invalid",
                params={"value": value},
            )

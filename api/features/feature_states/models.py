import typing
from typing import Literal

from django.conf import settings
from django.db import models

from features.value_types import (
    BOOLEAN,
    FEATURE_STATE_VALUE_TYPES,
    INTEGER,
    STRING,
)

FeatureValueType = Literal["string", "integer", "boolean"]


class AbstractBaseFeatureValueModel(models.Model):
    class Meta:
        abstract = True

    type = models.CharField(
        max_length=10,
        choices=FEATURE_STATE_VALUE_TYPES,
        default=STRING,
        null=True,
        blank=True,
    )
    boolean_value = models.BooleanField(null=True, blank=True)
    integer_value = models.IntegerField(null=True, blank=True)
    string_value = models.CharField(
        null=True, max_length=settings.FEATURE_VALUE_LIMIT, blank=True
    )

    @property
    def value(self) -> typing.Union[str, int, bool]:
        return {  # type: ignore[return-value]
            INTEGER: self.integer_value,
            STRING: self.string_value,
            BOOLEAN: self.boolean_value,
        }.get(
            self.type,  # type: ignore[arg-type]
            self.string_value,
        )

    def set_value(self, value: str, type_: FeatureValueType) -> None:
        typed_value: str | int | bool
        match type_:
            case "string":
                typed_value = value
                field = "string_value"
                type_const = STRING
            case "integer":
                try:
                    typed_value = int(value)
                except ValueError:
                    raise ValueError(f"'{value}' is not a valid integer")
                field = "integer_value"
                type_const = INTEGER
            case "boolean":
                if value.lower() not in ("true", "false"):
                    raise ValueError(
                        f"'{value}' is not a valid boolean (use 'true' or 'false')"
                    )
                typed_value = value.lower() == "true"
                field = "boolean_value"
                type_const = BOOLEAN
            case _:
                raise ValueError(
                    f"'{type_}' is not a valid type (use 'string', 'integer', or 'boolean')"
                )

        self.string_value = None
        self.integer_value = None
        self.boolean_value = None
        setattr(self, field, typed_value)
        self.type = type_const

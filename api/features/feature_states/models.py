import typing

from django.conf import settings
from django.db import models

from features.value_types import (
    BOOLEAN,
    FEATURE_STATE_VALUE_TYPES,
    INTEGER,
    STRING,
)


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
        return {
            INTEGER: self.integer_value,
            STRING: self.string_value,
            BOOLEAN: self.boolean_value,
        }.get(self.type, self.string_value)

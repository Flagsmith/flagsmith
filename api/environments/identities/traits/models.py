import typing
from copy import deepcopy
from typing import TYPE_CHECKING

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from simple_history.models import HistoricalRecords

from environments.identities.traits.exceptions import TraitPersistenceError
from environments.models import BOOLEAN, FLOAT, INTEGER, STRING

if TYPE_CHECKING:
    from environments.identities.models import Identity


@python_2_unicode_compatible
class Trait(models.Model):
    TRAIT_VALUE_TYPES = (
        (INTEGER, "Integer"),
        (STRING, "String"),
        (BOOLEAN, "Boolean"),
        (FLOAT, "Float"),
    )

    identity = models.ForeignKey(
        "identities.Identity", related_name="identity_traits", on_delete=models.CASCADE
    )
    trait_key = models.CharField(max_length=200)
    value_type = models.CharField(
        max_length=10, choices=TRAIT_VALUE_TYPES, default=STRING, null=True, blank=True
    )
    boolean_value = models.NullBooleanField(null=True, blank=True)
    integer_value = models.IntegerField(null=True, blank=True)
    string_value = models.CharField(null=True, max_length=2000, blank=True)
    float_value = models.FloatField(null=True, blank=True)

    created_date = models.DateTimeField("DateCreated", auto_now_add=True)

    class Meta:
        verbose_name_plural = "User Traits"
        unique_together = ("trait_key", "identity")
        ordering = ["id"]
        # hard code the table name after moving from the environments app to prevent
        # issues with production deployment due to multi server configuration.
        db_table = "environments_trait"

    @property
    def trait_value(self):
        return self.get_trait_value()

    def get_trait_value(self):
        try:
            value_type = self.value_type
        except ObjectDoesNotExist:
            return None

        type_mapping = {
            INTEGER: self.integer_value,
            STRING: self.string_value,
            BOOLEAN: self.boolean_value,
            FLOAT: self.float_value,
        }

        return type_mapping.get(value_type)

    @staticmethod
    def get_trait_value_key_name(tv_type):
        return {
            INTEGER: "integer_value",
            BOOLEAN: "boolean_value",
            STRING: "string_value",
            FLOAT: "float_value",
        }.get(
            tv_type, "string_value"
        )  # The default was chosen for backwards compatibility

    @staticmethod
    def generate_trait_value_data(value: typing.Any):
        """
        Takes the value and returns dictionary
        to use for passing into trait value serializer

        :param value: trait value of variable type or deserialized output from TraitValueField
        :return: dictionary to pass directly into trait serializer
        """
        accepted_types = (STRING, INTEGER, BOOLEAN, FLOAT)

        # this method is called from multiple places in the code, some of which use
        # the data that has been deserialized by TraitValueField, this conditional
        # logic allows us to handle both cases
        # TODO: tidy this up (probably when we move to storing traits in dynamo?)
        if isinstance(value, dict) and value.get("type"):
            tv_type = value["type"]
            value = value["value"]
        else:
            tv_type = type(value).__name__

        return {
            # Default to string if not an anticipate type value to keep backwards compatibility.
            "value_type": tv_type if tv_type in accepted_types else STRING,
            Trait.get_trait_value_key_name(tv_type): value,
        }

    def __str__(self):
        return "Identity: %s - %s" % (self.identity.identifier, self.trait_key)

    def clone(self, identity: "Identity") -> "Trait":
        clone = deepcopy(self)
        clone.id = None
        clone.identity = identity
        clone.save()
        return clone

    def save(self, *args, **kwargs):
        if not self.identity.environment.project.organisation.persist_trait_data:
            # this is a final line of defense to ensure that traits are never saved
            # for organisations which have the flag set to not persist trait data
            raise TraitPersistenceError(
                "Not possible to persist traits for this organisation."
            )

        return super(Trait, self).save(*args, **kwargs)

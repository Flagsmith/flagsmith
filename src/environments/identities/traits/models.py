from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from simple_history.models import HistoricalRecords

from environments.identities.traits.exceptions import TraitPersistenceError
from environments.models import INTEGER, STRING, BOOLEAN, FLOAT


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
    def generate_trait_value_data(value):
        """
        Takes the value and returns dictionary
        to use for passing into trait value serializer

        :param value: trait value of variable type
        :return: dictionary to pass directly into trait serializer
        """
        tv_type = type(value).__name__
        accepted_types = (STRING, INTEGER, BOOLEAN, FLOAT)

        return {
            # Default to string if not an anticipate type value to keep backwards compatibility.
            "value_type": tv_type if tv_type in accepted_types else STRING,
            Trait.get_trait_value_key_name(tv_type): value,
        }

    def __str__(self):
        return "Identity: %s - %s" % (self.identity.identifier, self.trait_key)

    def save(self, *args, **kwargs):
        if not self.identity.environment.project.organisation.persist_trait_data:
            # this is a final line of defense to ensure that traits are never saved
            # for organisations which have the flag set to not persist trait data
            raise TraitPersistenceError(
                "Not possible to persist traits for this organisation."
            )

        return super(Trait, self).save(*args, **kwargs)

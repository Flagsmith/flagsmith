from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from simple_history.models import HistoricalRecords

from .tasks import trigger_feature_state_change_webhooks
from .helpers import get_boolean_from_string, get_integer_from_string, get_value_type
from ..constants import INTEGER, STRING, BOOLEAN, CONFIG

FEATURE_STATE_VALUE_TYPES = (
    (INTEGER, "Integer"),
    (STRING, "String"),
    (BOOLEAN, "Boolean"),
)


@python_2_unicode_compatible
class FeatureState(models.Model):
    feature = models.ForeignKey(
        "features.Feature", related_name="feature_states", on_delete=models.CASCADE
    )
    environment = models.ForeignKey(
        "environments.Environment",
        related_name="feature_states",
        null=True,
        on_delete=models.CASCADE,
    )
    identity = models.ForeignKey(
        "identities.Identity",
        related_name="identity_features",
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
    )
    feature_segment = models.ForeignKey(
        "features.FeatureSegment",
        related_name="feature_states",
        null=True,
        blank=True,
        default=None,
        on_delete=models.CASCADE,
    )

    enabled = models.BooleanField(default=False)
    history = HistoricalRecords(table_name="features_historicalfeaturestate")

    class Meta:
        unique_together = (
            ("feature", "environment", "identity"),
            ("feature", "environment", "feature_segment"),
        )
        ordering = ["id"]
        db_table = "features_featurestate"

    def __gt__(self, other):
        """
        Checks if the current feature state is higher priority that the provided feature state.

        :param other: (FeatureState) the feature state to compare the priority of
        :return: True if self is higher priority than other
        """
        if self.environment != other.environment:
            raise ValueError(
                "Cannot compare feature states as they belong to different environments."
            )

        if self.feature != other.feature:
            raise ValueError(
                "Cannot compare feature states as they belong to different features."
            )

        if self.identity:
            # identity is the highest priority so we can always return true
            if other.identity and self.identity != other.identity:
                raise ValueError(
                    "Cannot compare feature states as they are for different identities."
                )
            return True

        if self.feature_segment:
            # Return true if other_feature_state has a lower priority feature segment and not an identity overridden
            # flag, else False.
            return not (other.identity or self.feature_segment < other.feature_segment)

        # if we've reached here, then self is just the environment default. In this case, other is higher priority if
        # it has a feature_segment or an identity
        return not (other.feature_segment or other.identity)

    def get_feature_state_value(self):
        if self.feature_segment:
            return self.feature_segment.get_value()

        try:
            value_type = self.feature_state_value.type
        except ObjectDoesNotExist:
            return None

        type_mapping = {
            INTEGER: self.feature_state_value.integer_value,
            STRING: self.feature_state_value.string_value,
            BOOLEAN: self.feature_state_value.boolean_value,
        }

        return type_mapping.get(value_type)

    @property
    def previous_feature_state_value(self):
        try:
            history_instance = self.feature_state_value.history.first()
        except ObjectDoesNotExist:
            return None

        previous_feature_state_value = history_instance.prev_record

        if previous_feature_state_value:
            value_type = previous_feature_state_value.type

            type_mapping = {
                INTEGER: previous_feature_state_value.integer_value,
                STRING: previous_feature_state_value.string_value,
                BOOLEAN: previous_feature_state_value.boolean_value,
            }

            return type_mapping.get(value_type)

    def save(self, *args, **kwargs):
        # prevent duplicate feature states being created for an environment
        if (
            not self.pk
            and FeatureState.objects.filter(
                environment=self.environment, feature=self.feature
            ).exists()
            and not (self.identity or self.feature_segment)
        ):
            raise ValidationError(
                "Feature state already exists for this environment and feature"
            )

        super(FeatureState, self).save(*args, **kwargs)

        # create default feature state value for feature state
        # note: this is get_or_create since feature state values are updated separately, and hence if this is set to
        # update_or_create, it overwrites the FSV with the initial value again
        # Note: feature segments are handled differently as they have their own values
        if not self.feature_segment and self.feature.type == CONFIG:
            FeatureStateValue.objects.get_or_create(
                feature_state=self, defaults=self._get_defaults()
            )
        # TODO: move this to an async call using celery or django-rq
        trigger_feature_state_change_webhooks(self)

    def _get_defaults(self):
        if self.feature_segment:
            return self._get_defaults_for_segment_feature_state()
        else:
            return self._get_defaults_for_environment_feature_state()

    def _get_defaults_for_segment_feature_state(self):
        defaults = {"type": self.feature_segment.value_type}

        key_name = self._get_feature_state_key_name(self.feature_segment.value_type)

        if self.feature_segment.value_type == BOOLEAN:
            if type(self.feature_segment.value) == BOOLEAN:
                defaults[key_name] = self.feature_segment.value
            else:
                defaults[key_name] = get_boolean_from_string(self.feature_segment.value)
        elif self.feature_segment.value_type == INTEGER:
            defaults[key_name] = get_integer_from_string(self.feature_segment.value)
        else:
            defaults[key_name] = self.feature_segment.value

        return defaults

    def _get_defaults_for_environment_feature_state(self):
        if not (self.feature.initial_value or self.feature.initial_value is False):
            return None

        value = self.feature.initial_value
        type = get_value_type(value)
        defaults = {"type": type}

        key_name = self._get_feature_state_key_name(type)
        if type == BOOLEAN:
            defaults[key_name] = get_boolean_from_string(value)
        elif type == INTEGER:
            defaults[key_name] = get_integer_from_string(value)
        else:
            defaults[key_name] = value

        return defaults

    @staticmethod
    def _get_feature_state_key_name(fsv_type):
        return {
            INTEGER: "integer_value",
            BOOLEAN: "boolean_value",
            STRING: "string_value",
        }.get(
            fsv_type, "string_value"
        )  # The default was chosen for backwards compatibility

    def generate_feature_state_value_data(self, value):
        """
        Takes the value of a feature state to generate a feature state value and returns dictionary
        to use for passing into feature state value serializer

        :param value: feature state value of variable type
        :return: dictionary to pass directly into feature state value serializer
        """
        fsv_type = type(value).__name__
        accepted_types = (STRING, INTEGER, BOOLEAN)

        return {
            # Default to string if not an anticipate type value to keep backwards compatibility.
            "type": fsv_type if fsv_type in accepted_types else STRING,
            "feature_state": self.id,
            self._get_feature_state_key_name(fsv_type): value,
        }

    def __str__(self):
        if self.environment is not None:
            return "Project %s - Environment %s - Feature %s - Enabled: %r" % (
                self.environment.project.name,
                self.environment.name,
                self.feature.name,
                self.enabled,
            )
        elif self.identity is not None:
            return "Identity %s - Feature %s - Enabled: %r" % (
                self.identity.identifier,
                self.feature.name,
                self.enabled,
            )
        else:
            return "Feature %s - Enabled: %r" % (self.feature.name, self.enabled)


class FeatureStateValue(models.Model):
    feature_state = models.OneToOneField(
        FeatureState, related_name="feature_state_value", on_delete=models.CASCADE
    )

    type = models.CharField(
        max_length=10,
        choices=FEATURE_STATE_VALUE_TYPES,
        default=STRING,
        null=True,
        blank=True,
    )
    boolean_value = models.NullBooleanField(null=True, blank=True)
    integer_value = models.IntegerField(null=True, blank=True)
    string_value = models.CharField(null=True, max_length=2000, blank=True)
    history = HistoricalRecords(table_name="features_historicalfeaturestatevalue")

    class Meta:
        db_table = "features_featurestatevalue"

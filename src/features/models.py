# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import (NON_FIELD_ERRORS, ObjectDoesNotExist,
                                    ValidationError)
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords

from features.utils import get_boolean_from_string, get_integer_from_string, INTEGER, STRING, BOOLEAN
from projects.models import Project

# Feature Types
FLAG = 'FLAG'
CONFIG = 'CONFIG'

FEATURE_STATE_VALUE_TYPES = (
    (INTEGER, 'Integer'),
    (STRING, 'String'),
    (BOOLEAN, 'Boolean')
)


@python_2_unicode_compatible
class Feature(models.Model):
    FEATURE_TYPES = (
        (FLAG, 'Feature Flag'),
        (CONFIG, 'Remote Config')
    )

    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    project = models.ForeignKey(
        Project,
        related_name='features',
        help_text=_(
            "Changing the project selected will remove previous Feature States for the previously "
            "associated projects Environments that are related to this Feature. New default "
            "Feature States will be created for the new selected projects Environments for this "
            "Feature."
        )
    )
    initial_value = models.CharField(max_length=2000, null=True, default=None)
    description = models.TextField(null=True, blank=True)
    default_enabled = models.BooleanField(default=False)
    type = models.CharField(max_length=50, choices=FEATURE_TYPES, default=FLAG)
    history = HistoricalRecords()

    class Meta:
        ordering = ['id']
        # Note: uniqueness is changed to reference lowercase name in explicit SQL in the migrations
        unique_together = ("name", "project")

    def save(self, *args, **kwargs):
        """
        Override save method to initialise feature states for all environments
        """
        if self.pk:
            old_feature = Feature.objects.get(pk=self.pk)
            if old_feature.project != self.project:
                FeatureState.objects.filter(
                    feature=self,
                    environment=old_feature.project.environments.values_list(
                        'pk', flat=True),
                ).all().delete()

        super(Feature, self).save(*args, **kwargs)

        # create feature states for all environments in the project
        environments = self.project.environments.all()
        for env in environments:
            FeatureState.objects.update_or_create(
                feature=self,
                environment=env,
                identity=None,
                defaults={
                    'enabled': self.default_enabled
                },
            )

    def validate_unique(self, *args, **kwargs):
        """
        Checks unique constraints on the model and raises ``ValidationError``
        if any failed.
        """
        super(Feature, self).validate_unique(*args, **kwargs)

        if Feature.objects.filter(project=self.project, name__iexact=self.name).exists():
            raise ValidationError(
                {
                    NON_FIELD_ERRORS: [
                        "Feature with that name already exists for this project. Note that feature "
                        "names are case insensitive.",
                    ],
                }
            )

    def __str__(self):
        return "Project %s - Feature %s" % (self.project.name, self.name)


def get_next_segment_priority(feature):
    feature_segments = FeatureSegment.objects.filter(feature=feature).order_by('-priority')
    if feature_segments.count() == 0:
        return 1
    else:
        return feature_segments.first().priority + 1


@python_2_unicode_compatible
class FeatureSegment(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name="feature_segments")
    segment = models.ForeignKey('segments.Segment', related_name="feature_segments")
    priority = models.IntegerField(blank=True, null=True)
    enabled = models.BooleanField(default=False)
    value = models.CharField(max_length=2000, blank=True, null=True)
    value_type = models.CharField(choices=FEATURE_STATE_VALUE_TYPES, max_length=50, blank=True, null=True)

    class Meta:
        unique_together = [('feature', 'segment'), ('feature', 'priority')]

    def save(self, *args, **kwargs):
        if not self.pk and not self.priority:
            # intialise priority field on object creation if not set
            self.priority = get_next_segment_priority(self.feature)

        super(FeatureSegment, self).save(*args, **kwargs)

        # create feature states
        for environment in self.feature.project.environments.all():
            fs, _ = FeatureState.objects.get_or_create(environment=environment, feature=self.feature,
                                                       feature_segment=self)
            fs.enabled = self.enabled
            fs.save()

    def __str__(self):
        return "FeatureSegment for " + self.feature.name + " with priority " + str(self.priority)


@python_2_unicode_compatible
class FeatureState(models.Model):
    feature = models.ForeignKey(Feature, related_name='feature_states')
    environment = models.ForeignKey('environments.Environment', related_name='feature_states',
                                    null=True)
    identity = models.ForeignKey('environments.Identity', related_name='identity_features',
                                 null=True, default=None, blank=True)
    feature_segment = models.ForeignKey(FeatureSegment, related_name='feature_states', null=True, blank=True,
                                        default=None)

    enabled = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        unique_together = (("feature", "environment", "identity"), ("feature", "environment", "feature_segment"))
        ordering = ['id']

    def get_feature_state_value(self):
        try:
            value_type = self.feature_state_value.type
        except ObjectDoesNotExist:
            return None

        type_mapping = {
            INTEGER: self.feature_state_value.integer_value,
            STRING: self.feature_state_value.string_value,
            BOOLEAN: self.feature_state_value.boolean_value
        }

        return type_mapping.get(value_type)

    def save(self, *args, **kwargs):
        super(FeatureState, self).save(*args, **kwargs)

        # create default feature state value for feature state
        FeatureStateValue.objects.get_or_create(
            feature_state=self,
            defaults=self._get_defaults()
        )

    def _get_defaults(self):
        if self.feature_segment:
            return self._get_defaults_for_segment_feature_state()
        else:
            return {
                'string_value': self.feature.initial_value
            }

    def _get_defaults_for_segment_feature_state(self):
        defaults = {
            'type': self.feature_segment.value_type
        }

        key_name = self._get_feature_state_key_name(self.feature_segment.value_type)

        if self.feature_segment.value_type == BOOLEAN:
            defaults[key_name] = get_boolean_from_string(self.feature_segment.value)
        elif self.feature_segment.value_type == INTEGER:
            defaults[key_name] = get_integer_from_string(self.feature_segment.value)
        else:
            defaults[key_name] = self.feature_segment.value

        return defaults

    @staticmethod
    def _get_feature_state_key_name(fsv_type):
        return {
            INTEGER: "integer_value",
            BOOLEAN: "boolean_value",
            STRING: "string_value",
        }.get(fsv_type, "string_value")  # The default was chosen for backwards compatibility

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
            self._get_feature_state_key_name(fsv_type): value
        }

    def __str__(self):
        if self.environment is not None:
            return "Project %s - Environment %s - Feature %s - Enabled: %r" % \
                   (self.environment.project.name,
                    self.environment.name, self.feature.name,
                    self.enabled)
        elif self.identity is not None:
            return "Identity %s - Feature %s - Enabled: %r" % (self.identity.identifier,
                                                               self.feature.name, self.enabled)
        else:
            return "Feature %s - Enabled: %r" % (self.feature.name, self.enabled)


class FeatureStateValue(models.Model):
    feature_state = models.OneToOneField(FeatureState, related_name='feature_state_value')

    type = models.CharField(max_length=10, choices=FEATURE_STATE_VALUE_TYPES, default=STRING,
                            null=True, blank=True)
    boolean_value = models.NullBooleanField(null=True, blank=True)
    integer_value = models.IntegerField(null=True, blank=True)
    string_value = models.CharField(null=True, max_length=2000, blank=True)
    history = HistoricalRecords()

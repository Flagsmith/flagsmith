from __future__ import unicode_literals

from django.core.exceptions import (NON_FIELD_ERRORS, ObjectDoesNotExist,
                                    ValidationError)
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from ordered_model.models import OrderedModelBase
from simple_history.models import HistoricalRecords

from features.helpers import get_correctly_typed_value
from features.tasks import trigger_feature_state_change_webhooks
from features.utils import get_boolean_from_string, get_integer_from_string, INTEGER, STRING, BOOLEAN, get_value_type
from projects.models import Project
from util.logging import get_logger

logger = get_logger(__name__)

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
            'Changing the project selected will remove previous Feature States for the previously '
            'associated projects Environments that are related to this Feature. New default '
            'Feature States will be created for the new selected projects Environments for this '
            'Feature.'
        ),
        on_delete=models.CASCADE
    )
    initial_value = models.CharField(max_length=2000, null=True, default=None)
    description = models.TextField(null=True, blank=True)
    default_enabled = models.BooleanField(default=False)
    type = models.CharField(max_length=50, choices=FEATURE_TYPES, default=FLAG)
    history = HistoricalRecords()

    class Meta:
        ordering = ['id']
        # Note: uniqueness is changed to reference lowercase name in explicit SQL in the migrations
        unique_together = ('name', 'project')

    def save(self, *args, **kwargs):
        '''
        Override save method to initialise feature states for all environments
        '''
        if self.pk:
            # If the feature has moved to a new project, delete the feature states from the old project
            old_feature = Feature.objects.get(pk=self.pk)
            if old_feature.project != self.project:
                FeatureState.objects.filter(
                    feature=self,
                    environment__in=old_feature.project.environments.all(),
                ).delete()

        super(Feature, self).save(*args, **kwargs)

        # create feature states for all environments in the project
        environments = self.project.environments.all()
        for env in environments:
            FeatureState.objects.update_or_create(
                feature=self,
                environment=env,
                identity=None,
                feature_segment=None,
                defaults={
                    'enabled': self.default_enabled
                },
            )

    def validate_unique(self, *args, **kwargs):
        '''
        Checks unique constraints on the model and raises ``ValidationError``
        if any failed.
        '''
        super(Feature, self).validate_unique(*args, **kwargs)

        if Feature.objects.filter(project=self.project, name__iexact=self.name).exists():
            raise ValidationError(
                {
                    NON_FIELD_ERRORS: [
                        'Feature with that name already exists for this project. Note that feature '
                        'names are case insensitive.',
                    ],
                }
            )

    def __str__(self):
        return 'Project %s - Feature %s' % (self.project.name, self.name)


def get_next_segment_priority(feature):
    feature_segments = FeatureSegment.objects.filter(feature=feature).order_by('-priority')
    if feature_segments.count() == 0:
        return 1
    else:
        return feature_segments.first().priority + 1


@python_2_unicode_compatible
class FeatureSegment(OrderedModelBase):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='feature_segments')
    segment = models.ForeignKey('segments.Segment', related_name='feature_segments', on_delete=models.CASCADE)
    environment = models.ForeignKey(
        'environments.Environment', on_delete=models.CASCADE, related_name='feature_segments'
    )

    enabled = models.BooleanField(default=False)
    value = models.CharField(max_length=2000, blank=True, null=True)
    value_type = models.CharField(choices=FEATURE_STATE_VALUE_TYPES, max_length=50, blank=True, null=True)

    # specific attributes for managing the order of feature segments
    priority = models.PositiveIntegerField(editable=False, db_index=True)
    order_field_name = 'priority'
    order_with_respect_to = ('feature', 'environment')

    # used for audit purposes
    history = HistoricalRecords()

    class Meta:
        unique_together = ('feature', 'environment', 'segment')
        ordering = ('priority',)

    def save(self, *args, **kwargs):
        super(FeatureSegment, self).save(*args, **kwargs)

        # update or create feature state for environment
        FeatureState.objects.update_or_create(
            environment=self.environment, feature=self.feature, feature_segment=self, defaults={"enabled": self.enabled}
        )

    def __str__(self):
        return 'FeatureSegment for ' + self.feature.name + ' with priority ' + str(self.priority)

    # noinspection PyTypeChecker
    def get_value(self):
        return get_correctly_typed_value(self.value_type, self.value)

    def __lt__(self, other):
        '''
        Kind of counter intuitive but since priority 1 is highest, we want to check if priority is GREATER than the
        priority of the other feature segment.
        '''
        return other and self.priority > other.priority


@python_2_unicode_compatible
class FeatureState(models.Model):
    feature = models.ForeignKey(Feature, related_name='feature_states', on_delete=models.CASCADE)
    environment = models.ForeignKey('environments.Environment', related_name='feature_states', null=True,
                                    on_delete=models.CASCADE)
    identity = models.ForeignKey('environments.Identity', related_name='identity_features',
                                 null=True, default=None, blank=True, on_delete=models.CASCADE)
    feature_segment = models.ForeignKey(FeatureSegment, related_name='feature_states', null=True, blank=True,
                                        default=None, on_delete=models.CASCADE)

    enabled = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        unique_together = (('feature', 'environment', 'identity'), ('feature', 'environment', 'feature_segment'))
        ordering = ['id']

    def __gt__(self, other):
        '''
        Checks if the current feature state is higher priority that the provided feature state.

        :param other: (FeatureState) the feature state to compare the priority of
        :return: True if self is higher priority than other
        '''
        if self.environment != other.environment:
            raise ValueError('Cannot compare feature states as they belong to different environments.')

        if self.feature != other.feature:
            raise ValueError('Cannot compare feature states as they belong to different features.')

        if self.identity:
            # identity is the highest priority so we can always return true
            if other.identity and self.identity != other.identity:
                raise ValueError('Cannot compare feature states as they are for different identities.')
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
            BOOLEAN: self.feature_state_value.boolean_value
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
                BOOLEAN: previous_feature_state_value.boolean_value
            }

            return type_mapping.get(value_type)

    def save(self, *args, **kwargs):
        # prevent duplicate feature states being created for an environment
        if not self.pk and FeatureState.objects.filter(environment=self.environment, feature=self.feature).exists() \
                and not (self.identity or self.feature_segment):
            raise ValidationError('Feature state already exists for this environment and feature')

        super(FeatureState, self).save(*args, **kwargs)

        # create default feature state value for feature state
        # note: this is get_or_create since feature state values are updated separately, and hence if this is set to
        # update_or_create, it overwrites the FSV with the initial value again
        # Note: feature segments are handled differently as they have their own values
        if not self.feature_segment:
            FeatureStateValue.objects.get_or_create(
                feature_state=self,
                defaults=self._get_defaults()
            )
        # TODO: move this to an async call using celery or django-rq
        trigger_feature_state_change_webhooks(self)

    def _get_defaults(self):
        if self.feature_segment:
            return self._get_defaults_for_segment_feature_state()
        else:
            return self._get_defaults_for_environment_feature_state()

    def _get_defaults_for_segment_feature_state(self):
        defaults = {
            'type': self.feature_segment.value_type
        }

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
        defaults = {
            'type': type
        }

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
            INTEGER: 'integer_value',
            BOOLEAN: 'boolean_value',
            STRING: 'string_value',
        }.get(fsv_type, 'string_value')  # The default was chosen for backwards compatibility

    def generate_feature_state_value_data(self, value):
        '''
        Takes the value of a feature state to generate a feature state value and returns dictionary
        to use for passing into feature state value serializer

        :param value: feature state value of variable type
        :return: dictionary to pass directly into feature state value serializer
        '''
        fsv_type = type(value).__name__
        accepted_types = (STRING, INTEGER, BOOLEAN)

        return {
            # Default to string if not an anticipate type value to keep backwards compatibility.
            'type': fsv_type if fsv_type in accepted_types else STRING,
            'feature_state': self.id,
            self._get_feature_state_key_name(fsv_type): value
        }

    def __str__(self):
        if self.environment is not None:
            return 'Project %s - Environment %s - Feature %s - Enabled: %r' % \
                   (self.environment.project.name,
                    self.environment.name, self.feature.name,
                    self.enabled)
        elif self.identity is not None:
            return 'Identity %s - Feature %s - Enabled: %r' % (self.identity.identifier,
                                                               self.feature.name, self.enabled)
        else:
            return 'Feature %s - Enabled: %r' % (self.feature.name, self.enabled)


class FeatureStateValue(models.Model):
    feature_state = models.OneToOneField(FeatureState, related_name='feature_state_value', on_delete=models.CASCADE)

    type = models.CharField(max_length=10, choices=FEATURE_STATE_VALUE_TYPES, default=STRING,
                            null=True, blank=True)
    boolean_value = models.NullBooleanField(null=True, blank=True)
    integer_value = models.IntegerField(null=True, blank=True)
    string_value = models.CharField(null=True, max_length=2000, blank=True)
    history = HistoricalRecords()

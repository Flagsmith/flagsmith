from __future__ import unicode_literals

from django.core.exceptions import (NON_FIELD_ERRORS, ValidationError)
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from ordered_model.models import OrderedModelBase
from simple_history.models import HistoricalRecords

from features.constants import FLAG, CONFIG
from features.feature_states.models import FEATURE_STATE_VALUE_TYPES, FeatureState
from features.feature_states.helpers import get_correctly_typed_value
from projects.models import Project
from projects.tags.models import Tag
from util.logging import get_logger

logger = get_logger(__name__)


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
            'Changing the project selected will remove previous Feature States for the previously'
            'associated projects Environments that are related to this Feature. New default '
            'Feature States will be created for the new selected projects Environments for this '
            'Feature. Also this will remove any Tags associated with a feature as Tags are Project defined'
        ),
        on_delete=models.CASCADE
    )
    initial_value = models.CharField(max_length=2000, null=True, default=None)
    description = models.TextField(null=True, blank=True)
    default_enabled = models.BooleanField(default=False)
    type = models.CharField(max_length=50, choices=FEATURE_TYPES, default=FLAG)
    history = HistoricalRecords()
    tags = models.ManyToManyField(Tag, blank=True)

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

        # handle case insensitive names per project, as above check allows it
        if Feature.objects.filter(project=self.project, name__iexact=self.name).exclude(pk=self.pk).exists():
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

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import (ObjectDoesNotExist)
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords

from app.utils import create_hash
from environments.exceptions import EnvironmentHeaderNotPresentError
from features.models import FeatureState
from projects.models import Project

# User Trait Value Types
INTEGER = "int"
STRING = "unicode"
BOOLEAN = "bool"


@python_2_unicode_compatible
class Environment(models.Model):
    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    project = models.ForeignKey(
        Project,
        related_name="environments",
        help_text=_(
            "Changing the project selected will remove all previous Feature States for the "
            "previously associated projects Features that are related to this Environment. New "
            "default Feature States will be created for the new selected projects Features for "
            "this Environment."
        )
    )
    api_key = models.CharField(default=create_hash, unique=True, max_length=100)
    webhooks_enabled = models.BooleanField(default=False, help_text='DEPRECATED FIELD.')
    webhook_url = models.URLField(null=True, blank=True, help_text='DEPRECATED FIELD.')

    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        """
        Override save method to initialise feature states for all features in new environment
        """
        requires_feature_state_creation = True if not self.pk else False
        if self.pk:
            old_environment = Environment.objects.get(pk=self.pk)
            if old_environment.project != self.project:
                FeatureState.objects.filter(
                    feature__in=old_environment.project.features.values_list('pk', flat=True),
                    environment=self,
                ).all().delete()
                requires_feature_state_creation = True

        super(Environment, self).save(*args, **kwargs)

        if requires_feature_state_creation:
            # also create feature states for all features in the project
            features = self.project.features.all()
            for feature in features:
                FeatureState.objects.create(
                    feature=feature,
                    environment=self,
                    identity=None,
                    enabled=feature.default_enabled
                )

    def __str__(self):
        return "Project %s - Environment %s" % (self.project.name, self.name)

    @staticmethod
    def get_environment_from_request(request):
        try:
            environment_key = request.META['HTTP_X_ENVIRONMENT_KEY']
        except KeyError:
            raise EnvironmentHeaderNotPresentError

        return Environment.objects.select_related('project', 'project__organisation').get(
            api_key=environment_key)


@python_2_unicode_compatible
class Identity(models.Model):
    identifier = models.CharField(max_length=2000)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    environment = models.ForeignKey(Environment, related_name='identities')

    class Meta:
        verbose_name_plural = "Identities"
        ordering = ['id']
        unique_together = ('environment', 'identifier',)

    def get_all_feature_states(self):
        # get all features that have been overridden for an identity
        # and only feature states for features which are not associated with an identity
        # and are not in the to be overridden
        feature_ids_overridden_by_segment = self.get_segment_feature_states().values_list('feature__id', flat=True)
        flags = FeatureState.objects.filter(
            Q(environment=self.environment) &
            (
                # first get all feature states that have been explicitly overridden for the identity
                Q(identity=self) |

                # next get all feature states that have been overridden for any segments the identity matches, ignoring
                # any that are explicitly overridden for the identity as that still takes priority
                # TODO: does this take priority into account?
                Q(feature_segment__segment__in=self.get_segments()) & ~Q(
                    feature__id__in=self.identity_features.values_list(
                        'feature__id', flat=True
                    )
                ) |

                # finally, get all feature states for the environment that haven't been overridden
                (
                    Q(identity=None) &
                    Q(feature_segment=None) &
                    ~Q(
                        feature__id__in=self.identity_features.values_list(
                            'feature__id', flat=True
                        )
                    ) &
                    ~Q(
                        feature__id__in=feature_ids_overridden_by_segment
                    )
                )
            ),
        ).select_related("feature", "feature_state_value")

        return flags

    def get_segments(self):
        segments = []
        for segment in self.environment.project.segments.all():
            if segment.does_identity_match(self):
                segments.append(segment)
        return segments

    def get_segment_feature_states(self):
        return FeatureState.objects.filter(environment=self.environment,
                                           feature_segment__segment__in=self.get_segments())

    def get_all_user_traits(self):
        # get all all user traits for an identity
        traits = Trait.objects.filter(identity=self)
        return traits

    def __str__(self):
        return "Account %s" % self.identifier


@python_2_unicode_compatible
class Trait(models.Model):
    TRAIT_VALUE_TYPES = (
        (INTEGER, 'Integer'),
        (STRING, 'String'),
        (BOOLEAN, 'Boolean')
    )

    identity = models.ForeignKey('environments.Identity', related_name='identity_traits')
    trait_key = models.CharField(max_length=200)
    value_type = models.CharField(max_length=10, choices=TRAIT_VALUE_TYPES, default=STRING,
                                  null=True, blank=True)
    boolean_value = models.NullBooleanField(null=True, blank=True)
    integer_value = models.IntegerField(null=True, blank=True)
    string_value = models.CharField(null=True, max_length=2000, blank=True)

    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "User Traits"
        unique_together = ("trait_key", "identity")
        ordering = ['id']

    def get_trait_value(self):
        try:
            value_type = self.value_type
        except ObjectDoesNotExist:
            return None

        type_mapping = {
            INTEGER: self.integer_value,
            STRING: self.string_value,
            BOOLEAN: self.boolean_value
        }

        return type_mapping.get(value_type)

    @staticmethod
    def _get_trait_key_name(tv_type):
        return {
            INTEGER: "integer_value",
            BOOLEAN: "boolean_value",
            STRING: "string_value",
        }.get(tv_type, "string_value")  # The default was chosen for backwards compatibility

    @staticmethod
    def generate_trait_value_data(value):
        """
        Takes the value and returns dictionary
        to use for passing into trait value serializer

        :param value: trait value of variable type
        :return: dictionary to pass directly into trait serializer
        """
        tv_type = type(value).__name__
        accepted_types = (STRING, INTEGER, BOOLEAN)

        return {
            # Default to string if not an anticipate type value to keep backwards compatibility.
            "value_type": tv_type if tv_type in accepted_types else STRING,
            Trait._get_trait_key_name(tv_type): value
        }

    def __str__(self):
        return "Identity: %s - %s" % (self.identity.identifier, self.trait_key)


class Webhook(models.Model):
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='webhooks')
    url = models.URLField()
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

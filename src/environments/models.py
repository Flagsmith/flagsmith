# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import (ObjectDoesNotExist)
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords

from app.utils import create_hash
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
    webhooks_enabled = models.BooleanField(default=False)
    webhook_url = models.URLField(null=True, blank=True)

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


@python_2_unicode_compatible
class Identity(models.Model):
    identifier = models.CharField(max_length=2000)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    environment = models.ForeignKey(Environment, related_name='identities')

    class Meta:
        verbose_name_plural = "Identities"
        ordering = ['id']

    def get_all_feature_states(self):
        # get all features that have been overridden for an identity
        # and only feature states for features which are not associated with an identity
        # and are not in the to be overridden
        flags = FeatureState.objects.filter(
            Q(environment=self.environment) &
            (
                Q(identity=self) |
                (
                    Q(identity=None) &
                    ~Q(
                        feature__id__in=self.identity_features.filter(identity=self).values_list(
                            'feature__id', flat=True
                        )
                    )
                )
            ),
        )
        return flags

    def get_all_user_traits(self):
        # get all features that have been overridden for an identity
        # and only feature states for features which are not associated with an identity
        # and are not in the to be overridden

        traits = Trait.objects.filter(identity=self)

        return traits

    def __str__(self):
        return "Account %s" % self.identifier


@python_2_unicode_compatible
class Trait(models.Model):
    trait_key = models.CharField(max_length=200)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    updated_date = models.DateTimeField('DateUpdate', auto_now_add=True)
    identity = models.ForeignKey('environments.Identity', related_name='identity_traits')
    history = HistoricalRecords()

    class Meta:
        verbose_name_plural = "User Traits"
        unique_together = ("trait_key", "identity")
        ordering = ['id']

    def get_trait_value(self):
        try:
            value_type = self.trait_value.type
        except ObjectDoesNotExist:
            return None

        type_mapping = {
            INTEGER: self.trait_value.integer_value,
            STRING: self.trait_value.string_value,
            BOOLEAN: self.trait_value.boolean_value
        }

        return type_mapping.get(value_type)

    def save(self, *args, **kwargs):
        super(Trait, self).save(*args, **kwargs)

        # create default trait value for user trait
        # TraitValue.objects.get_or_create(
        #     trait=self,
        #     defaults={
        #         'string_value': self.feature.initial_value
        #     }
        # )

    @staticmethod
    def _get_trait_key_name(fsv_type):
        return {
            INTEGER: "integer_value",
            BOOLEAN: "boolean_value",
            STRING: "string_value",
        }.get(fsv_type, "string_value")  # The default was chosen for backwards compatibility

    def generate_trait_value_data(self, value):
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
            "trait": self.id,
            self._get_trait_key_name(fsv_type): value
        }

    def __str__(self):
        return "Identity: %s - Trait: %s " % (self.identity.identifier, self.trait_key)


# Holds the actual value for User Trait
class TraitValue(models.Model):
    TRAIT_VALUE_TYPES = (
        (INTEGER, 'Integer'),
        (STRING, 'String'),
        (BOOLEAN, 'Boolean')
    )

    trait = models.OneToOneField(
        Trait, related_name='trait_value')
    type = models.CharField(max_length=10, choices=TRAIT_VALUE_TYPES, default=STRING,
                            null=True, blank=True)
    boolean_value = models.NullBooleanField(null=True, blank=True)
    integer_value = models.IntegerField(null=True, blank=True)
    string_value = models.CharField(null=True, max_length=2000, blank=True)
    history = HistoricalRecords()

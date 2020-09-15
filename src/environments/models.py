# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import typing

from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import (ObjectDoesNotExist)
from django.db import models
from django.db.models import Q
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
from simple_history.models import HistoricalRecords

from app.utils import create_hash
from environments.exceptions import EnvironmentHeaderNotPresentError, \
    TraitPersistenceError
from features.models import FeatureState
from permissions.models import BasePermissionModelABC, PermissionModel, ENVIRONMENT_PERMISSION_TYPE
from projects.models import Project

# User Trait Value Types
INTEGER = "int"
STRING = "unicode"
BOOLEAN = "bool"

environment_cache = caches[settings.ENVIRONMENT_CACHE_LOCATION]


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
        ),
        on_delete=models.CASCADE
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

    @classmethod
    def get_from_cache(cls, api_key):
        environment = environment_cache.get(api_key)
        if not environment:
            environment = Environment.objects.select_related('project', 'project__organisation').get(api_key=api_key)
            # TODO: replace the hard coded cache timeout with an environment variable
            #  until we merge in the pulumi stuff, however, we'll have too many conflicts
            environment_cache.set(environment.api_key, environment, timeout=60)
        return environment


@python_2_unicode_compatible
class Trait(models.Model):
    TRAIT_VALUE_TYPES = (
        (INTEGER, 'Integer'),
        (STRING, 'String'),
        (BOOLEAN, 'Boolean')
    )

    identity = models.ForeignKey('environments.Identity', related_name='identity_traits', on_delete=models.CASCADE)
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
            BOOLEAN: self.boolean_value
        }

        return type_mapping.get(value_type)

    @staticmethod
    def get_trait_value_key_name(tv_type):
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
            Trait.get_trait_value_key_name(tv_type): value
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


@python_2_unicode_compatible
class Identity(models.Model):
    identifier = models.CharField(max_length=2000)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    environment = models.ForeignKey(Environment, related_name='identities', on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Identities"
        ordering = ['id']
        unique_together = ('environment', 'identifier',)

    def get_all_feature_states(self, traits: typing.List[Trait] = None):
        """
        Get all feature states for an identity. This method returns a single flag for each feature
        in the identity's environment's project. The flag returned is the correct flag based on the
        priorities as follows (highest -> lowest):

            1. Identity - flag override for this specific identity
            2. Segment - flag overridden for a segment this identity belongs to
            3. Environment - default value for the environment

        :return: (list) flags for an identity with the correct values based on identity / segment priorities
        """
        segments = self.get_segments(traits=traits)

        # define sub queries
        belongs_to_environment_query = Q(environment=self.environment)
        overridden_for_identity_query = Q(identity=self)
        overridden_for_segment_query = Q(
            feature_segment__segment__in=segments, feature_segment__environment=self.environment
        )
        environment_default_query = Q(identity=None, feature_segment=None)

        # define the full query
        full_query = belongs_to_environment_query & (
            overridden_for_identity_query | overridden_for_segment_query | environment_default_query
        )

        select_related_args = ['feature', 'feature_state_value', 'feature_segment', 'feature_segment__segment']

        all_flags = FeatureState.objects.select_related(*select_related_args).filter(full_query)

        # iterate over all the flags and build a dictionary keyed on feature with the highest priority flag
        # for the given identity as the value.
        identity_flags = {}
        for flag in all_flags:
            if flag.feature_id not in identity_flags:
                identity_flags[flag.feature_id] = flag
            else:
                if flag > identity_flags[flag.feature_id]:
                    identity_flags[flag.feature_id] = flag

        return list(identity_flags.values())

    def get_segments(self, traits: typing.List[Trait] = None):
        segments = []
        for segment in self.environment.project.segments.all():
            if segment.does_identity_match(self, traits=traits):
                segments.append(segment)
        return segments

    def get_all_user_traits(self):
        # get all all user traits for an identity
        traits = Trait.objects.filter(identity=self)
        return traits

    def __str__(self):
        return "Account %s" % self.identifier


class Webhook(models.Model):
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_name='webhooks')
    url = models.URLField()
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class EnvironmentPermissionManager(models.Manager):
    def get_queryset(self):
        return super(EnvironmentPermissionManager, self).get_queryset().filter(type=ENVIRONMENT_PERMISSION_TYPE)


class EnvironmentPermissionModel(PermissionModel):
    class Meta:
        proxy = True

    objects = EnvironmentPermissionManager()


class UserEnvironmentPermission(BasePermissionModelABC):
    user = models.ForeignKey('users.FFAdminUser', on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_query_name='userpermission')


class UserPermissionGroupEnvironmentPermission(BasePermissionModelABC):
    group = models.ForeignKey('users.UserPermissionGroup', on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE, related_query_name='grouppermission')

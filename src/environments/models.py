# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from app.utils import create_hash
from features.models import FeatureState
from projects.models import Project


class Environment(models.Model):
    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    project = models.ForeignKey(Project, related_name="environments")
    api_key = models.CharField(default=create_hash, unique=True, max_length=100)

    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        """
        Override save method to initialise feature states for all features in new environment
        """
        super(Environment, self).save(*args, **kwargs)

        # also create feature states for all features in the project
        features = self.project.features.all()
        for feature in features:
            FeatureState.objects.create(feature=feature, environment=self, identity=None,
                                        enabled=feature.default_enabled)

    def __str__(self):
        return "Project %s - Environment %s" % (self.project.name, self.name)

    def __unicode__(self):
        return "Project %s - Environment %s" % (self.project.name, self.name)


class Identity(models.Model):
    identifier = models.CharField(max_length=2000)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    environment = models.ForeignKey(Environment, related_name='identities')

    class Meta:
        verbose_name_plural = "Identities"
        ordering = ['id']

    def get_all_feature_states(self):
        # get all features that have been overridden for an identity
        identity_flags = self.identity_features.filter(identity=self)

        override_features = [flag.feature for flag in identity_flags]

        # get only feature states for features which are not associated with an identity
        # and are not in the to be overridden generated above
        environment_flags = self.environment.feature_states.filter(environment=self.environment,
                                                                   identity=None)\
            .exclude(feature__in=override_features)

        return identity_flags, environment_flags

    def __str__(self):
        return "Account %s" % self.identifier

    def __unicode__(self):
        return "Account %s" % self.identifier

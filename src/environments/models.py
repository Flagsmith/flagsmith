# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.cache import caches
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from app.utils import create_hash
from environments.exceptions import EnvironmentHeaderNotPresentError
from features.models import FeatureState
from projects.models import Project
from util.history.custom_simple_history import NonWritingHistoricalRecords
from util.logging import get_logger

logger = get_logger(__name__)

# User Trait Value Types
INTEGER = "int"
STRING = "unicode"
BOOLEAN = "bool"
FLOAT = "float"

environment_cache = caches[settings.ENVIRONMENT_CACHE_LOCATION]


@python_2_unicode_compatible
class Environment(models.Model):
    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)
    project = models.ForeignKey(
        Project,
        related_name="environments",
        help_text=_(
            "Changing the project selected will remove all previous Feature States for the "
            "previously associated projects Features that are related to this Environment. New "
            "default Feature States will be created for the new selected projects Features for "
            "this Environment."
        ),
        on_delete=models.CASCADE,
    )
    api_key = models.CharField(default=create_hash, unique=True, max_length=100)
    webhooks_enabled = models.BooleanField(default=False, help_text="DEPRECATED FIELD.")
    webhook_url = models.URLField(null=True, blank=True, help_text="DEPRECATED FIELD.")

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        """
        Override save method to initialise feature states for all features in new environment
        """
        requires_feature_state_creation = True if not self.pk else False
        if self.pk:
            old_environment = Environment.objects.get(pk=self.pk)
            if old_environment.project != self.project:
                FeatureState.objects.filter(
                    feature__in=old_environment.project.features.values_list(
                        "pk", flat=True
                    ),
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
                    enabled=feature.default_enabled,
                )

    def __str__(self):
        return "Project %s - Environment %s" % (self.project.name, self.name)

    @staticmethod
    def get_environment_from_request(request):
        try:
            environment_key = request.META["HTTP_X_ENVIRONMENT_KEY"]
        except KeyError:
            raise EnvironmentHeaderNotPresentError

        return Environment.objects.select_related(
            "project", "project__organisation"
        ).get(api_key=environment_key)

    @classmethod
    def get_from_cache(cls, api_key):
        try:
            environment = environment_cache.get(api_key)
            if not environment:
                select_related_args = (
                    "project",
                    "project__organisation",
                    "amplitude_config",
                )
                environment = cls.objects.select_related(*select_related_args).get(
                    api_key=api_key
                )
                # TODO: replace the hard coded cache timeout with an environment variable
                #  until we merge in the pulumi stuff, however, we'll have too many conflicts
                environment_cache.set(environment.api_key, environment, timeout=60)
            return environment
        except cls.DoesNotExist as err:
            logger.error(
                "Environment with api_key %s does not exist. %s" % (api_key, err)
            )


class Webhook(models.Model):
    environment = models.ForeignKey(
        Environment, on_delete=models.CASCADE, related_name="webhooks"
    )
    url = models.URLField()
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

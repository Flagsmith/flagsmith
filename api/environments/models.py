# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import typing
from copy import deepcopy

import boto3
from core.request_origin import RequestOrigin
from django.conf import settings
from django.core.cache import caches
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_lifecycle import AFTER_CREATE, AFTER_SAVE, LifecycleModel, hook
from flag_engine.api.document_builders import (
    build_environment_api_key_document,
)
from rest_framework.request import Request

from app.utils import create_hash
from environments.api_keys import (
    generate_client_api_key,
    generate_server_api_key,
)
from environments.exceptions import EnvironmentHeaderNotPresentError
from environments.managers import EnvironmentManager
from features.models import FeatureState
from projects.models import Project
from webhooks.models import AbstractBaseWebhookModel

logger = logging.getLogger(__name__)
environment_cache = caches[settings.ENVIRONMENT_CACHE_LOCATION]


class Environment(LifecycleModel):
    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)
    description = models.TextField(null=True, blank=True)
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

    api_key = models.CharField(
        default=generate_client_api_key, unique=True, max_length=100
    )

    minimum_change_request_approvals = models.IntegerField(blank=True, null=True)

    webhooks_enabled = models.BooleanField(default=False, help_text="DEPRECATED FIELD.")
    webhook_url = models.URLField(null=True, blank=True, help_text="DEPRECATED FIELD.")

    allow_client_traits = models.BooleanField(
        default=True, help_text="Allows clients using the client API key to set traits."
    )

    objects = EnvironmentManager()

    class Meta:
        ordering = ["id"]

    @hook(AFTER_CREATE)
    def create_feature_states(self):
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

    def natural_key(self):
        return (self.api_key,)

    def clone(self, name: str, api_key: str = None) -> "Environment":
        """
        Creates a clone of the environment, related objects and returns the
        cloned object after saving it to the database.
        # NOTE: clone will not trigger create hooks
        """
        clone = deepcopy(self)
        clone.id = None
        clone.name = name
        clone.api_key = api_key if api_key else create_hash()
        clone.save()
        for feature_segment in self.feature_segments.all():
            feature_segment.clone(clone)

        # Since identities are closely tied to the enviroment
        # it does not make much sense to clone them, hence
        # only clone feature states without identities
        for feature_state in self.feature_states.filter(identity=None):
            feature_state.clone(clone, live_from=feature_state.live_from)

        return clone

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
            if not api_key:
                logger.warning("Requested environment with null api_key.")
                return None

            environment = environment_cache.get(api_key)
            if not environment:
                select_related_args = (
                    "project",
                    "project__organisation",
                    "mixpanel_config",
                    "segment_config",
                    "amplitude_config",
                    "heap_config",
                    "dynatrace_config",
                )
                environment = (
                    cls.objects.select_related(*select_related_args)
                    .filter(Q(api_key=api_key) | Q(api_keys__key=api_key))
                    .distinct()
                    .get()
                )
                environment_cache.set(environment.api_key, environment, timeout=60)
            return environment
        except cls.DoesNotExist:
            logger.info("Environment with api_key %s does not exist" % api_key)

    def get_feature_state(
        self, feature_id: int, filter_kwargs: dict = None
    ) -> typing.Optional[FeatureState]:
        """
        Get the corresponding feature state in an environment for a given feature id.
        Optionally override the kwargs passed to filter to get the feature state for
        a feature segment or identity.
        """

        if not filter_kwargs:
            filter_kwargs = {"feature_segment_id": None, "identity_id": None}

        return next(
            filter(
                lambda fs: fs.feature.id == feature_id,
                self.feature_states.filter(**filter_kwargs),
            )
        )

    def trait_persistence_allowed(self, request: Request) -> bool:
        return (
            self.allow_client_traits
            or getattr(request, "originated_from", RequestOrigin.CLIENT)
            == RequestOrigin.SERVER
        )


class Webhook(AbstractBaseWebhookModel):
    environment = models.ForeignKey(
        Environment, on_delete=models.CASCADE, related_name="webhooks"
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


dynamo_api_key_table = None
if settings.ENVIRONMENTS_API_KEY_TABLE_NAME_DYNAMO:
    dynamo_api_key_table = boto3.resource("dynamodb").Table(
        settings.ENVIRONMENTS_API_KEY_TABLE_NAME_DYNAMO
    )


class EnvironmentAPIKey(LifecycleModel):
    """
    These API keys are only currently used for server side integrations.
    """

    environment = models.ForeignKey(
        Environment, on_delete=models.CASCADE, related_name="api_keys"
    )
    key = models.CharField(default=generate_server_api_key, max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    expires_at = models.DateTimeField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def natural_key(self):
        return (self.key,)

    @property
    def is_valid(self) -> bool:
        return self.active and (not self.expires_at or self.expires_at > timezone.now())

    @hook(AFTER_SAVE)
    def send_to_dynamo(self):
        if not dynamo_api_key_table:
            return
        env_key_dict = build_environment_api_key_document(self)
        dynamo_api_key_table.put_item(Item=env_key_dict)

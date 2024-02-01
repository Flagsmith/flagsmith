# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import typing
from copy import deepcopy

from core.models import abstract_base_auditable_model_factory
from core.request_origin import RequestOrigin
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.cache import caches
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django_lifecycle import (
    AFTER_CREATE,
    AFTER_DELETE,
    AFTER_SAVE,
    AFTER_UPDATE,
    BEFORE_UPDATE,
    LifecycleModel,
    hook,
)
from rest_framework.request import Request
from softdelete.models import SoftDeleteObject

from app.utils import create_hash
from audit.constants import (
    ENVIRONMENT_CREATED_MESSAGE,
    ENVIRONMENT_UPDATED_MESSAGE,
)
from audit.related_object_type import RelatedObjectType
from environments.api_keys import (
    generate_client_api_key,
    generate_server_api_key,
)
from environments.dynamodb import (
    DynamoEnvironmentAPIKeyWrapper,
    DynamoEnvironmentV2Wrapper,
    DynamoEnvironmentWrapper,
)
from environments.exceptions import EnvironmentHeaderNotPresentError
from environments.managers import EnvironmentManager
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.exceptions import FeatureVersioningError
from metadata.models import Metadata
from projects.models import IdentityOverridesV2MigrationStatus, Project
from segments.models import Segment
from util.mappers import map_environment_to_environment_document
from webhooks.models import AbstractBaseExportableWebhookModel

logger = logging.getLogger(__name__)

environment_cache = caches[settings.ENVIRONMENT_CACHE_NAME]
environment_document_cache = caches[settings.ENVIRONMENT_DOCUMENT_CACHE_LOCATION]
environment_segments_cache = caches[settings.ENVIRONMENT_SEGMENTS_CACHE_NAME]
bad_environments_cache = caches[settings.BAD_ENVIRONMENTS_CACHE_LOCATION]

# Intialize the dynamo environment wrapper(s) globaly
environment_wrapper = DynamoEnvironmentWrapper()
environment_v2_wrapper = DynamoEnvironmentV2Wrapper()
environment_api_key_wrapper = DynamoEnvironmentAPIKeyWrapper()


class Environment(
    LifecycleModel,
    abstract_base_auditable_model_factory(
        change_details_excluded_fields=["updated_at"]
    ),
    SoftDeleteObject,
):
    history_record_class_path = "environments.models.HistoricalEnvironment"
    related_object_type = RelatedObjectType.ENVIRONMENT

    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)
    description = models.TextField(null=True, blank=True, max_length=20000)
    project = models.ForeignKey(
        "projects.Project",
        related_name="environments",
        help_text=_(
            "Changing the project selected will remove all previous Feature States for"
            " the previously associated projects Features that are related to this"
            " Environment. New default Feature States will be created for the new"
            " selected projects Features for this Environment."
        ),
        # Cascade deletes are decouple from the Django ORM. See this PR for details.
        # https://github.com/Flagsmith/flagsmith/pull/3360/
        on_delete=models.DO_NOTHING,
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
    updated_at = models.DateTimeField(
        default=timezone.now,
        help_text="Tracks changes to self and related entities, e.g. FeatureStates.",
    )
    banner_text = models.CharField(null=True, blank=True, max_length=255)
    banner_colour = models.CharField(
        null=True, blank=True, max_length=7, help_text="hex code for the banner colour"
    )
    metadata = GenericRelation(Metadata)

    hide_disabled_flags = models.BooleanField(
        null=True,
        blank=True,
        help_text=(
            "If true will exclude flags from SDK which are disabled. NOTE: If set, this"
            " will override the project `hide_disabled_flags`"
        ),
    )
    use_identity_composite_key_for_hashing = models.BooleanField(
        default=True,
        help_text=(
            "Enable this to have consistent multivariate and percentage split evaluations "
            "across all SDKs (in local and server side mode)"
        ),
        db_column="use_mv_v2_evaluation",  # see https://github.com/Flagsmith/flagsmith/issues/2186
    )
    hide_sensitive_data = models.BooleanField(
        default=False,
        help_text="If true, will hide sensitive data(e.g: traits, description etc) from the SDK endpoints",
    )

    objects = EnvironmentManager()

    use_v2_feature_versioning = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    @hook(AFTER_CREATE)
    def create_feature_states(self):
        FeatureState.create_initial_feature_states_for_environment(environment=self)

    @hook(AFTER_UPDATE)
    def clear_environment_cache(self):
        # TODO: this could rebuild the cache itself (using an async task)
        environment_cache.delete(self.initial_value("api_key"))

    @hook(BEFORE_UPDATE, when="use_v2_feature_versioning", was=True, is_now=False)
    def validate_use_v2_feature_versioning(self):
        raise FeatureVersioningError("Cannot revert from v2 feature versioning.")

    @hook(AFTER_DELETE)
    def delete_from_dynamo(self):
        if self.project.enable_dynamo_db and environment_wrapper.is_enabled:
            from environments.tasks import delete_environment_from_dynamo

            delete_environment_from_dynamo.delay(args=(self.api_key, self.id))

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

        # Since identities are closely tied to the environment
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

            if cls.is_bad_key(api_key):
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
                base_qs = cls.objects.select_related(*select_related_args).defer(
                    "description"
                )
                qs_for_embedded_api_key = base_qs.filter(api_key=api_key)
                qs_for_fk_api_key = base_qs.filter(api_keys__key=api_key)

                environment = qs_for_embedded_api_key.union(qs_for_fk_api_key).get()
                environment_cache.set(
                    api_key, environment, timeout=settings.ENVIRONMENT_CACHE_SECONDS
                )
            return environment
        except cls.DoesNotExist:
            cls.set_bad_key(api_key)
            logger.info("Environment with api_key %s does not exist" % api_key)

    @classmethod
    def write_environments_to_dynamodb(
        cls, environment_id: int = None, project_id: int = None
    ) -> None:
        # use a list to make sure the entire qs is evaluated up front
        environments_filter = (
            Q(id=environment_id) if environment_id else Q(project_id=project_id)
        )
        environments = list(
            cls.objects.filter_for_document_builder(environments_filter)
        )
        if not environments:
            return

        # grab the first project and verify that each environment is for the same
        # project (which should always be the case). Since we're working with fairly
        # small querysets here, this shouldn't have a noticeable impact on performance.
        project: Project | None = getattr(environments[0], "project", None)
        for environment in environments[1:]:
            if not environment.project == project:
                raise RuntimeError("Environments must all belong to the same project.")

        if not all([project, project.enable_dynamo_db, environment_wrapper.is_enabled]):
            return

        environment_wrapper.write_environments(environments)

        if (
            project.identity_overrides_v2_migration_status
            == IdentityOverridesV2MigrationStatus.COMPLETE
            and environment_v2_wrapper.is_enabled
        ):
            environment_v2_wrapper.write_environments(environments)

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

    @staticmethod
    def is_bad_key(environment_key: str) -> bool:
        return (
            settings.CACHE_BAD_ENVIRONMENTS_SECONDS > 0
            and bad_environments_cache.get(environment_key, 0)
            >= settings.CACHE_BAD_ENVIRONMENTS_AFTER_FAILURES
        )

    @staticmethod
    def set_bad_key(environment_key: str) -> None:
        if settings.CACHE_BAD_ENVIRONMENTS_SECONDS:
            current_count = bad_environments_cache.get(environment_key, 0)
            bad_environments_cache.set(
                environment_key,
                current_count + 1,
                timeout=settings.CACHE_BAD_ENVIRONMENTS_SECONDS,
            )

    def trait_persistence_allowed(self, request: Request) -> bool:
        return (
            self.allow_client_traits
            or getattr(request, "originated_from", RequestOrigin.CLIENT)
            == RequestOrigin.SERVER
        )

    def get_segments_from_cache(self) -> typing.List[Segment]:
        """
        Get any segments that have been overridden in this environment.
        """
        segments = environment_segments_cache.get(self.id)
        if not segments:
            segments = list(
                Segment.objects.filter(
                    feature_segments__feature_states__environment=self
                ).prefetch_related(
                    "rules",
                    "rules__conditions",
                    "rules__rules",
                    "rules__rules__conditions",
                    "rules__rules__rules",
                )
            )
            environment_segments_cache.set(self.id, segments)
        return segments

    @classmethod
    def get_environment_document(
        cls,
        api_key: str,
    ) -> dict[str, typing.Any]:
        if settings.CACHE_ENVIRONMENT_DOCUMENT_SECONDS > 0:
            return cls._get_environment_document_from_cache(api_key)
        return cls._get_environment_document_from_db(api_key)

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:
        return ENVIRONMENT_CREATED_MESSAGE % self.name

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        return ENVIRONMENT_UPDATED_MESSAGE % self.name

    def get_hide_disabled_flags(self) -> bool:
        if self.hide_disabled_flags is not None:
            return self.hide_disabled_flags

        return self.project.hide_disabled_flags

    @classmethod
    def _get_environment_document_from_cache(
        cls,
        api_key: str,
    ) -> dict[str, typing.Any]:
        environment_document = environment_document_cache.get(api_key)
        if not environment_document:
            environment_document = cls._get_environment_document_from_db(api_key)
            environment_document_cache.set(api_key, environment_document)
        return environment_document

    @classmethod
    def _get_environment_document_from_db(
        cls,
        api_key: str,
    ) -> dict[str, typing.Any]:
        environment = cls.objects.filter_for_document_builder(api_key=api_key).get()
        return map_environment_to_environment_document(environment)

    def _get_environment(self):
        return self

    def _get_project(self):
        return self.project


class Webhook(AbstractBaseExportableWebhookModel):
    environment = models.ForeignKey(
        Environment, on_delete=models.CASCADE, related_name="webhooks"
    )
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def generate_webhook_feature_state_data(
        feature: Feature,
        environment: Environment,
        enabled: bool,
        value: typing.Union[str, int, bool, type(None)],
        identity_id: typing.Union[int, str] = None,
        identity_identifier: str = None,
        feature_segment: FeatureSegment = None,
    ) -> dict:
        if (identity_id or identity_identifier) and not (
            identity_id and identity_identifier
        ):
            raise ValueError("Must provide both identity_id and identity_identifier.")

        if (identity_id and identity_identifier) and feature_segment:
            raise ValueError("Cannot provide identity information and feature segment")

        # TODO: refactor to use a serializer / schema
        data = {
            "feature": {
                "id": feature.id,
                "created_date": feature.created_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "default_enabled": feature.default_enabled,
                "description": feature.description,
                "initial_value": feature.initial_value,
                "name": feature.name,
                "project": {
                    "id": feature.project_id,
                    "name": feature.project.name,
                },
                "type": feature.type,
            },
            "environment": {
                "id": environment.id,
                "name": environment.name,
            },
            "identity": identity_id,
            "identity_identifier": identity_identifier,
            "feature_segment": None,
            "enabled": enabled,
            "feature_state_value": value,
        }
        if feature_segment:
            data["feature_segment"] = {
                "segment": {
                    "id": feature_segment.segment_id,
                    "name": feature_segment.segment.name,
                    "description": feature_segment.segment.description,
                },
                "priority": feature_segment.priority,
            }
        return data


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

    @hook(AFTER_SAVE, when="_should_update_dynamo", is_now=True)
    def send_to_dynamo(self):
        environment_api_key_wrapper.write_api_key(self)

    @hook(AFTER_DELETE, when="_should_update_dynamo", is_now=True)
    def delete_from_dynamo(self):
        environment_api_key_wrapper.delete_api_key(self.key)

    @property
    def _should_update_dynamo(self) -> bool:
        return (
            self.environment.project.enable_dynamo_db
            and environment_api_key_wrapper.is_enabled
        )

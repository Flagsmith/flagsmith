import datetime
import json
import typing
import uuid
from copy import deepcopy

from core.models import (
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory,
)
from django.conf import settings
from django.db import models
from django.db.models import Index
from django.utils import timezone
from django_lifecycle import LifecycleModelMixin
from softdelete.models import SoftDeleteObject

from api_keys.models import MasterAPIKey
from features.versioning.exceptions import FeatureVersioningError
from features.versioning.managers import EnvironmentFeatureVersionManager
from features.versioning.signals import environment_feature_version_published

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from features.models import Feature
    from users.models import FFAdminUser


class EnvironmentFeatureVersion(
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(),
):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    environment = models.ForeignKey(
        "environments.Environment", on_delete=models.CASCADE
    )
    feature = models.ForeignKey("features.Feature", on_delete=models.CASCADE)

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    published_at = models.DateTimeField(blank=True, null=True)
    live_from = models.DateTimeField(null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_environment_feature_versions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_by_api_key = models.ForeignKey(
        "api_keys.MasterAPIKey",
        related_name="created_environment_feature_versions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="published_environment_feature_versions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    published_by_api_key = models.ForeignKey(
        "api_keys.MasterAPIKey",
        related_name="published_environment_feature_versions",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    change_request = models.ForeignKey(
        "workflows_core.ChangeRequest",
        related_name="environment_feature_versions",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    objects = EnvironmentFeatureVersionManager()

    class Meta:
        indexes = [Index(fields=("environment", "feature"))]
        ordering = ("-live_from",)

    def __gt__(self, other):
        return self.is_live and (not other.is_live or self.live_from > other.live_from)

    @property
    def is_live(self) -> bool:
        return self.published and self.live_from <= timezone.now()

    @property
    def published(self) -> bool:
        return self.published_at is not None

    @classmethod
    def create_initial_version(
        cls, environment: "Environment", feature: "Feature"
    ) -> "EnvironmentFeatureVersion":
        """
        Create an initial version with all the current feature states
        for a feature / environment combination.
        """

        if not environment.use_v2_feature_versioning:
            raise FeatureVersioningError(
                "Cannot create initial version for environment using v1 versioning."
            )
        elif cls.objects.filter(environment=environment, feature=feature).exists():
            raise FeatureVersioningError(
                "Version already exists for this feature / environment combination."
            )

        return cls.objects.create(
            environment=environment, feature=feature, published_at=timezone.now()
        )

    def get_previous_version(self) -> typing.Optional["EnvironmentFeatureVersion"]:
        return (
            self.__class__.objects.filter(
                environment=self.environment,
                feature=self.feature,
                live_from__lt=self.live_from or timezone.now(),
                published_at__isnull=False,
            )
            .order_by("-live_from")
            .exclude(uuid=self.uuid)
            .first()
        )

    def publish(
        self,
        published_by: typing.Union["FFAdminUser", None] = None,
        published_by_api_key: MasterAPIKey | None = None,
        live_from: datetime.datetime | None = None,
        persist: bool = True,
    ) -> None:
        assert not (
            published_by and published_by_api_key
        ), "Version must be published by either a user or a MasterAPIKey"

        now = timezone.now()

        self.live_from = live_from or (self.live_from or now)
        self.published_at = now
        self.published_by = published_by
        self.published_by_api_key = published_by_api_key

        if persist:
            self.save()
            environment_feature_version_published.send(self.__class__, instance=self)

    def clone_to_environment(
        self, environment: "Environment"
    ) -> "EnvironmentFeatureVersion":
        _clone = deepcopy(self)

        _clone.uuid = None
        _clone.environment = environment

        _clone.save()
        return _clone


class VersionChangeSet(LifecycleModelMixin, SoftDeleteObject):
    change_request = models.ForeignKey(
        "workflows_core.ChangeRequest",
        on_delete=models.CASCADE,
        related_name="change_sets",
    )
    feature = models.ForeignKey(
        "features.Feature",
        on_delete=models.CASCADE,
    )
    live_from = models.DateTimeField(null=True)

    # TODO: should this be a JSON blob or actual feature states?
    #  Essentially it's the difference between approaches 1 & 2 here:
    #  https://www.notion.so/flagsmith/Versioned-Change-Requests-improvements-d6ecf07ff3274fe586141525dbc5203f
    feature_states_to_create = models.TextField(
        null=True,
        help_text="JSON blob describing the feature states that should be "
        "created when the change request is published",
    )
    feature_states_to_update = models.TextField(
        null=True,
        help_text="JSON blob describing the feature states that should be "
        "updated when the change request is published",
    )
    segment_ids_to_delete_overrides = models.TextField(
        null=True,
        help_text="JSON blob describing the segment overrides for which"
        "the segment overrides should be deleted when the change "
        "request is published",
    )

    def publish(self, created_by: "FFAdminUser") -> None:
        from features.versioning.serializers import (
            EnvironmentFeatureVersionCreateSerializer,
        )

        # TODO:
        #  - how do we handle live_from here - should it be on this model, or on the change request itself perhaps?
        #  - this is super hacky, is there another abstraction layer we can add (and reuse in the serializer
        #    as well perhaps?)
        #  - handle API keys
        #  - handle scheduled change requests
        #  - handle conflicts

        serializer = EnvironmentFeatureVersionCreateSerializer(
            data={
                "feature_states_to_create": json.loads(self.feature_states_to_create),
                "feature_states_to_update": json.loads(self.feature_states_to_update),
                "segment_ids_to_delete_overrides": json.loads(
                    self.segment_ids_to_delete_overrides
                ),
            }
        )
        serializer.is_valid(raise_exception=True)
        version: EnvironmentFeatureVersion = serializer.save(
            feature=self.feature,
            environment=self.change_request.environment,
            created_by=created_by,
        )
        version.publish(
            published_by=created_by, live_from=self.live_from or timezone.now()
        )

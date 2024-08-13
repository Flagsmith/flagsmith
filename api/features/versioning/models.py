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
from django_lifecycle import BEFORE_CREATE, LifecycleModelMixin, hook
from softdelete.models import SoftDeleteObject

from api_keys.models import MasterAPIKey
from features.versioning.dataclasses import Conflict
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    published_by = models.ForeignKey(
        "users.FFAdminUser",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    environment = models.ForeignKey(
        "environments.Environment", on_delete=models.CASCADE
    )

    change_request = models.ForeignKey(
        "workflows_core.ChangeRequest",
        on_delete=models.CASCADE,
        related_name="change_sets",
        blank=True,
        null=True,
    )
    environment_feature_version = models.ForeignKey(
        "feature_versioning.EnvironmentFeatureVersion",
        on_delete=models.CASCADE,
        # Needs to be blank/nullable since change sets
        # associated with a change request do not yet
        # have a version
        blank=True,
        null=True,
    )

    feature = models.ForeignKey(
        "features.Feature",
        on_delete=models.CASCADE,
    )
    live_from = models.DateTimeField(null=True)

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

    @hook(BEFORE_CREATE)
    def add_environment(self):
        if not self.environment_id:
            if self.change_request_id:
                self.environment = self.change_request.environment
            elif self.environment_feature_version_id:
                self.environment = self.environment_feature_version.environment
            else:
                raise RuntimeError(
                    "Version change set should belong to either a change request, or a version."
                )

    def get_parsed_feature_states_to_create(self) -> list[dict[str, typing.Any]]:
        if self.feature_states_to_create:
            return json.loads(self.feature_states_to_create)
        return []

    def get_parsed_feature_states_to_update(self) -> list[dict[str, typing.Any]]:
        if self.feature_states_to_update:
            return json.loads(self.feature_states_to_update)
        return []

    def get_parsed_segment_ids_to_delete_overrides(self) -> list[int]:
        if self.segment_ids_to_delete_overrides:
            return json.loads(self.segment_ids_to_delete_overrides)
        return []

    def publish(self, user: "FFAdminUser") -> None:
        from features.versioning.tasks import publish_version_change_set

        kwargs = {"version_change_set_id": self.id, "user_id": user.id}
        if not self.live_from or self.live_from < timezone.now():
            publish_version_change_set(**kwargs)
        else:
            kwargs["is_scheduled"] = True
            publish_version_change_set.delay(kwargs=kwargs, delay_until=self.live_from)

    def get_conflicts(self) -> list[Conflict]:
        if self.published_at:
            return []

        change_sets_since_creation = list(
            self.__class__.objects.filter(
                published_at__gte=self.created_at,
                feature=self.feature,
                environment=self.environment,
            ).select_related("change_request")
        )
        if not change_sets_since_creation:
            return []

        conflicts = [
            *self._get_conflicts_in_feature_states_to_update(
                change_sets_since_creation
            ),
            *self._get_conflicts_in_feature_states_to_create(
                change_sets_since_creation
            ),
            *self._get_conflicts_in_segment_ids_to_delete_overrides(
                change_sets_since_creation
            ),
        ]
        return conflicts

    def includes_change_to_environment_default(self) -> bool:
        for fs_to_update in self.get_parsed_feature_states_to_update():
            if fs_to_update["feature_segment"] is None:
                return True

        return False

    def includes_change_to_segment(self, segment_id: int) -> bool:
        modified_segment_ids = {
            *self.get_parsed_segment_ids_to_delete_overrides(),
            *[
                fs["feature_segment"]["segment"]
                for fs in filter(
                    lambda fs: fs["feature_segment"] is not None,
                    [
                        *self.get_parsed_feature_states_to_create(),
                        *self.get_parsed_feature_states_to_update(),
                    ],
                )
            ],
        }
        return segment_id in modified_segment_ids

    def _get_conflicts_in_feature_states_to_update(
        self, change_sets_since_creation: list["VersionChangeSet"]
    ) -> list[Conflict]:
        _conflicts = []
        for fs_to_update in self.get_parsed_feature_states_to_update():
            feature_segment = fs_to_update["feature_segment"]
            is_change_to_environment_default = feature_segment is None

            for change_set in change_sets_since_creation:
                if is_change_to_environment_default:
                    if change_set.includes_change_to_environment_default():
                        _conflicts.append(
                            Conflict(
                                original_cr_id=change_set.change_request_id,
                                published_at=change_set.published_at,
                            )
                        )
                elif change_set.includes_change_to_segment(feature_segment["segment"]):
                    _conflicts.append(
                        Conflict(
                            original_cr_id=change_set.change_request_id,
                            segment_id=fs_to_update["feature_segment"]["segment"],
                            published_at=change_set.published_at,
                        )
                    )

        return _conflicts

    def _get_conflicts_in_feature_states_to_create(
        self, change_sets_since_creation: list["VersionChangeSet"]
    ) -> list[Conflict]:
        _conflicts = []
        for fs_to_create in self.get_parsed_feature_states_to_create():
            for change_set in change_sets_since_creation:
                # Note that feature states to create cannot be environment defaults so
                # must always have a feature segment
                if change_set.includes_change_to_segment(
                    fs_to_create["feature_segment"]["segment"]
                ):
                    _conflicts.append(
                        Conflict(
                            original_cr_id=change_set.change_request_id,
                            segment_id=fs_to_create["feature_segment"]["segment"],
                        )
                    )

        return _conflicts

    def _get_conflicts_in_segment_ids_to_delete_overrides(
        self, change_sets_since_create: list["VersionChangeSet"]
    ) -> list[Conflict]:
        _conflicts = []
        for segment_id in self.get_parsed_segment_ids_to_delete_overrides():
            for change_set in change_sets_since_create:
                if change_set.includes_change_to_segment(segment_id):
                    _conflicts.append(
                        Conflict(
                            original_cr_id=change_set.change_request_id,
                            segment_id=segment_id,
                        )
                    )

        return _conflicts

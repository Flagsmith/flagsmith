# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from core.models import SoftDeleteExportableModel
from django.conf import settings
from django.core.cache import caches
from django.db import models
from django.db.models import Count
from django_lifecycle import (
    AFTER_DELETE,
    AFTER_SAVE,
    AFTER_UPDATE,
    BEFORE_CREATE,
    LifecycleModelMixin,
    hook,
)

from environments.dynamodb import DynamoProjectMetadata
from organisations.models import Organisation
from permissions.models import (
    PROJECT_PERMISSION_TYPE,
    AbstractBasePermissionModel,
    PermissionModel,
)
from projects.managers import ProjectManager
from projects.services import get_project_segments_from_cache
from projects.tasks import (
    handle_cascade_delete,
    migrate_project_environments_to_v2,
    write_environments_to_dynamodb,
)

environment_cache = caches[settings.ENVIRONMENT_CACHE_NAME]


class EdgeV2MigrationStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", "Not Started"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    COMPLETE = "COMPLETE", "Complete"
    INCOMPLETE = "INCOMPLETE", "Incomplete (identity overrides skipped)"


class Project(LifecycleModelMixin, SoftDeleteExportableModel):
    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField("DateCreated", auto_now_add=True)
    organisation = models.ForeignKey(
        Organisation, related_name="projects", on_delete=models.CASCADE
    )
    hide_disabled_flags = models.BooleanField(
        default=False,
        help_text="If true will exclude flags from SDK which are " "disabled",
    )
    enable_dynamo_db = models.BooleanField(
        default=False,
        help_text="If true will sync environment data with dynamodb and allow access to dynamodb identities",
    )
    prevent_flag_defaults = models.BooleanField(
        default=False,
        help_text="Prevent defaults from being set in all environments when creating a feature.",
    )
    enable_realtime_updates = models.BooleanField(
        default=False,
        help_text="Enable this to trigger a realtime(sse) event whenever the value of a flag changes",
    )
    only_allow_lower_case_feature_names = models.BooleanField(
        default=True, help_text="Used by UI to validate feature names"
    )
    feature_name_regex = models.CharField(
        null=True,
        blank=True,
        max_length=255,
        help_text="Used for validating feature names",
    )
    max_segments_allowed = models.IntegerField(
        default=100, help_text="Max segments allowed for this project"
    )
    max_features_allowed = models.IntegerField(
        default=400, help_text="Max features allowed for this project"
    )
    max_segment_overrides_allowed = models.IntegerField(
        default=100,
        help_text="Max segments overrides allowed for any (one) environment within this project",
    )
    edge_v2_migration_status = models.CharField(
        max_length=50,
        choices=EdgeV2MigrationStatus.choices,
        # Note that the default is actually set dynamically by a lifecycle hook on create
        # since we need to know whether edge is enabled or not.
        default=EdgeV2MigrationStatus.NOT_STARTED,
        db_column="identity_overrides_v2_migration_status",
        help_text="[Edge V2 migration] Project migration status. Set to `IN_PROGRESS` to trigger migration start.",
    )
    edge_v2_migration_read_capacity_budget = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        help_text=(
            "[Edge V2 migration] Read capacity budget override. If project migration was finished with "
            "`INCOMPLETE` status, you can set it to a higher value than `EDGE_V2_MIGRATION_READ_CAPACITY_BUDGET` "
            "setting before restarting the migration."
        ),
    )
    stale_flags_limit_days = models.IntegerField(
        default=30,
        help_text="Number of days without modification in any environment before a flag is considered stale.",
    )
    minimum_change_request_approvals = models.IntegerField(blank=True, null=True)

    objects = ProjectManager()

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return "Project %s" % self.name

    @property
    def is_too_large(self) -> bool:
        return (
            self.features.count() > self.max_features_allowed
            or self.live_segment_count() > self.max_segments_allowed
            or self.environments.annotate(
                segment_override_count=Count("feature_segments")
            )
            .filter(segment_override_count__gt=self.max_segment_overrides_allowed)
            .exists()
        )

    # The following should be instance methods on `EdgeV2MigrationStatus`,
    # but the field value is coerced to `str` in some code paths
    # even when using `django-enum`:
    @property
    def edge_v2_environments_migrated(self) -> bool:
        return self.edge_v2_migration_status in (
            EdgeV2MigrationStatus.COMPLETE,
            EdgeV2MigrationStatus.INCOMPLETE,
        )

    @property
    def edge_v2_identity_overrides_migrated(self) -> bool:
        return self.edge_v2_migration_status == EdgeV2MigrationStatus.COMPLETE

    def get_segments_from_cache(self):
        return get_project_segments_from_cache(self.id)

    @hook(BEFORE_CREATE)
    def set_enable_dynamo_db(self):
        self.enable_dynamo_db = self.enable_dynamo_db or settings.EDGE_ENABLED

    @hook(BEFORE_CREATE)
    def set_edge_v2_migration_status(self):
        if settings.EDGE_ENABLED:
            self.edge_v2_migration_status = EdgeV2MigrationStatus.COMPLETE

    @hook(AFTER_SAVE)
    def clear_environments_cache(self):
        environment_cache.delete_many(
            list(self.environments.values_list("api_key", flat=True))
        )

    @hook(
        AFTER_SAVE,
        when="edge_v2_migration_status",
        has_changed=True,
        is_now=EdgeV2MigrationStatus.IN_PROGRESS,
    )
    def trigger_environments_v2_migration(self) -> None:
        migrate_project_environments_to_v2.delay(kwargs={"project_id": self.id})

    @hook(AFTER_UPDATE)
    def write_to_dynamo(self):
        write_environments_to_dynamodb.delay(kwargs={"project_id": self.id})

    @hook(AFTER_DELETE)
    def clean_up_dynamo(self):
        DynamoProjectMetadata(self.id).delete()

    @hook(AFTER_DELETE)
    def handle_cascade_delete(self) -> None:
        handle_cascade_delete.delay(kwargs={"project_id": self.id})

    @property
    def is_edge_project_by_default(self) -> bool:
        return bool(
            settings.EDGE_RELEASE_DATETIME
            and self.created_date >= settings.EDGE_RELEASE_DATETIME
        )

    def live_segment_count(self) -> int:
        from segments.models import Segment

        return Segment.live_objects.filter(project=self).count()

    def is_feature_name_valid(self, feature_name: str) -> bool:
        """
        Validate the feature name based on the feature_name_regex attribute.

        Since we always want to evaluate the regex against the whole string, we're wrapping the
        attribute value in ^(...)$. Note that ^(...)$ and ^^(...)$$ are equivalent (in case the
        attribute already has the boundaries defined)
        """
        return (
            not self.feature_name_regex
            or re.match(f"^{self.feature_name_regex}$", feature_name) is not None
        )

    @property
    def show_edge_identity_overrides_for_feature(self) -> bool:
        return self.edge_v2_migration_status == EdgeV2MigrationStatus.COMPLETE


class ProjectPermissionManager(models.Manager):
    def get_queryset(self):
        return (
            super(ProjectPermissionManager, self)
            .get_queryset()
            .filter(type=PROJECT_PERMISSION_TYPE)
        )


class ProjectPermissionModel(PermissionModel):
    class Meta:
        proxy = True

    objects = ProjectPermissionManager()


class UserPermissionGroupProjectPermission(AbstractBasePermissionModel):
    group = models.ForeignKey("users.UserPermissionGroup", on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_query_name="grouppermission"
    )
    admin = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["group", "project"], name="unique_group_project_permission"
            )
        ]


class UserProjectPermission(AbstractBasePermissionModel):
    user = models.ForeignKey(
        "users.FFAdminUser",
        on_delete=models.CASCADE,
        related_name="project_permissions",
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_query_name="userpermission"
    )
    admin = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "project"], name="unique_user_project_permission"
            )
        ]

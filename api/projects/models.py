# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.cache import caches
from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from organisations.models import Organisation
from permissions.models import (
    PROJECT_PERMISSION_TYPE,
    BasePermissionModelABC,
    PermissionModel,
)

project_segments_cache = caches[settings.PROJECT_SEGMENTS_CACHE_LOCATION]


@python_2_unicode_compatible
class Project(models.Model):
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
        help_text="If true will sync environment data with dynamodb for global API",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return "Project %s" % self.name

    def get_segments_from_cache(self):
        segments = project_segments_cache.get(self.id)

        if not segments:
            # This is optimised to account for rules nested one levels deep (since we
            # don't support anything above that from the UI at the moment). Anything
            # past that will require additional queries / thought on how to optimise.
            segments = self.segments.all().prefetch_related(
                "rules",
                "rules__conditions",
                "rules__rules",
                "rules__rules__conditions",
                "rules__rules__rules",
            )
            project_segments_cache.set(
                self.id, segments, timeout=settings.CACHE_PROJECT_SEGMENTS_SECONDS
            )

        return segments


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


class UserPermissionGroupProjectPermission(BasePermissionModelABC):
    group = models.ForeignKey("users.UserPermissionGroup", on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_query_name="grouppermission"
    )


class UserProjectPermission(BasePermissionModelABC):
    user = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_query_name="userpermission"
    )

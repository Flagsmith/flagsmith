# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from organisations.models import Organisation
from permissions.models import BasePermissionModelABC, PermissionModel, PROJECT_PERMISSION_TYPE


@python_2_unicode_compatible
class Project(models.Model):
    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    organisation = models.ForeignKey(Organisation, related_name='projects', on_delete=models.CASCADE)
    hide_disabled_flags = models.BooleanField(default=False, help_text='If true will exclude flags from SDK which are '
                                                                       'disabled')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return "Project %s" % self.name


class ProjectPermissionManager(models.Manager):
    def get_queryset(self):
        return super(ProjectPermissionManager, self).get_queryset().filter(type=PROJECT_PERMISSION_TYPE)


class ProjectPermissionModel(PermissionModel):
    class Meta:
        proxy = True

    objects = ProjectPermissionManager()


class UserPermissionGroupProjectPermission(BasePermissionModelABC):
    group = models.ForeignKey('users.UserPermissionGroup', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_query_name='grouppermission')


class UserProjectPermission(BasePermissionModelABC):
    user = models.ForeignKey('users.FFAdminUser', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_query_name='userpermission')

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from organisations.models import Organisation


@python_2_unicode_compatible
class Project(models.Model):
    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    organisation = models.ForeignKey(
        Organisation,
        related_name='projects',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return "Project %s" % self.name

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from organisations.models import Organisation


class Project(models.Model):
    name = models.CharField(max_length=2000)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    organisation = models.ForeignKey(Organisation, related_name='projects')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return "Project %s" % self.name

    def __unicode__(self):
        return "Project %s" % self.name

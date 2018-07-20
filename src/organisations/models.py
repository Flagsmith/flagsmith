# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Organisation(models.Model):
    name = models.CharField(max_length=2000)
    has_requested_features = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return "Org %s" % self.name

    def __unicode__(self):
        return "Org %s" % self.name

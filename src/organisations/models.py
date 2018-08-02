# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Organisation(models.Model):
    name = models.CharField(max_length=2000)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return "Org %s" % self.name

# -*- coding: utf-8 -*-
from django.db import models

from django.utils.encoding import python_2_unicode_compatible

from projects.models import Project


@python_2_unicode_compatible
class Segment(models.Model):
    name = models.CharField(max_length=2000)
    description = models.TextField(null=True, blank=True)
    rules = models.TextField(null=False, blank=False)
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, related_name="segments")

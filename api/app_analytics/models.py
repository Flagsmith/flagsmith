from django.db import models

from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation
from projects.models import Project


class Resource(models.IntegerChoices):
    FLAGS = 1
    IDENTITIES = 2
    TRAITS = 3
    ENVIRONMENT_DOCUMENT = 4


class APIUsage(models.Model):
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    host = models.CharField(max_length=255)
    resource = models.IntegerField(choices=Resource.choices)


class FeatureEvaluation(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    evaluation_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

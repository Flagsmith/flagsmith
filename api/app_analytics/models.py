from django.db import models


class Resource(models.IntegerChoices):
    FLAGS = 1
    IDENTITIES = 2
    TRAITS = 3
    ENVIRONMENT_DOCUMENT = 4


class APIUsageRaw(models.Model):
    environment_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    host = models.CharField(max_length=255)
    resource = models.IntegerField(choices=Resource.choices)

    class Meta:
        index_together = (("environment_id", "created_at"),)


class APIUsageBucket(models.Model):
    environment_id = models.PositiveIntegerField()
    resource = models.IntegerField(choices=Resource.choices)
    total_count = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    bucket_size = models.PositiveIntegerField(help_text="Bucket size in minutes")


class FeatureEvaluation(models.Model):
    feature_id = models.PositiveIntegerField()
    evaluation_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

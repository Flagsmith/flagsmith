from django.db import models


class Resource(models.IntegerChoices):
    FLAGS = 1
    IDENTITIES = 2
    TRAITS = 3
    ENVIRONMENT_DOCUMENT = 4

    @classmethod
    def get_lowercased_name(cls, resource: int) -> str:
        member = next(filter(lambda member: member.value == resource, cls), None)
        if not member:
            raise ValueError("Invalid resource: {resource}")

        return member.name.lower()

    @classmethod
    def get_from_resource_name(cls, resource: str) -> int:
        return (
            {
                "flags": cls.FLAGS,
                "identities": cls.IDENTITIES,
                "traits": cls.TRAITS,
                "environment-document": cls.ENVIRONMENT_DOCUMENT,
            }
            .get(resource)
            .value
        )


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


class FeatureEvaluationRaw(models.Model):
    feature_name = models.CharField(max_length=2000)
    environment_id = models.PositiveIntegerField()
    evaluation_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class FeatureEvaluationBucket(models.Model):
    feature_name = models.CharField(max_length=2000)
    environment_id = models.PositiveIntegerField()

    total_count = models.PositiveIntegerField()
    created_at = models.DateTimeField()
    bucket_size = models.PositiveIntegerField(help_text="Bucket size in minutes")

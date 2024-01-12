from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models
from django_lifecycle import BEFORE_CREATE, LifecycleModelMixin, hook


class Resource(models.IntegerChoices):
    FLAGS = 1
    IDENTITIES = 2
    TRAITS = 3
    ENVIRONMENT_DOCUMENT = 4

    @classmethod
    def get_lowercased_name(cls, resource: int) -> str:
        member = next(filter(lambda member: member.value == resource, cls), None)
        if not member:
            raise ValueError(f"Invalid resource: {resource}")

        return member.name.lower()

    @classmethod
    def get_from_resource_name(cls, resource: str) -> int:
        try:
            return getattr(cls, resource.upper().replace("-", "_")).value
        except (KeyError, AttributeError) as err:
            raise ValueError(f"Invalid resource: {resource}") from err


class APIUsageRaw(models.Model):
    environment_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    host = models.CharField(max_length=255)
    resource = models.IntegerField(choices=Resource.choices)

    class Meta:
        index_together = (("environment_id", "created_at"),)


class AbstractBucket(LifecycleModelMixin, models.Model):
    bucket_size = models.PositiveIntegerField(help_text="Bucket size in minutes")
    created_at = models.DateTimeField()
    total_count = models.PositiveIntegerField()
    environment_id = models.PositiveIntegerField()

    class Meta:
        abstract = True

    def check_overlapping_buckets(self, filters):
        overlapping_buckets = self.__class__.objects.filter(
            environment_id=self.environment_id,
            bucket_size=self.bucket_size,
            created_at__gte=self.created_at,
            created_at__lt=self.created_at + timedelta(minutes=self.bucket_size),
        )
        overlapping_buckets = overlapping_buckets.filter(filters)

        if overlapping_buckets.exists():
            raise ValidationError(
                "Cannot create bucket starting at %s with size %s minutes,"
                "because it overlaps with existing buckets"
                % (self.created_at, self.bucket_size),
            )


class APIUsageBucket(AbstractBucket):
    resource = models.IntegerField(choices=Resource.choices)

    @hook(BEFORE_CREATE)
    def check_overlapping_buckets(self):
        filter = models.Q(resource=self.resource)
        super().check_overlapping_buckets(filter)


class FeatureEvaluationRaw(models.Model):
    feature_name = models.CharField(db_index=True, max_length=2000)
    environment_id = models.PositiveIntegerField()
    evaluation_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    # Both stored for tracking multivariate split testing.
    identity_identifier = models.CharField(max_length=2000, null=True, default=None)
    enabled_when_evaluated = models.BooleanField(null=True, default=None)


class FeatureEvaluationBucket(AbstractBucket):
    feature_name = models.CharField(max_length=2000)

    @hook(BEFORE_CREATE)
    def check_overlapping_buckets(self):
        filter = models.Q(feature_name=self.feature_name)
        super().check_overlapping_buckets(filter)

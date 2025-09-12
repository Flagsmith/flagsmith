from datetime import timedelta

from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import ValidationError
from django.db import models
from django_lifecycle import (  # type: ignore[import-untyped]
    BEFORE_CREATE,
    LifecycleModelMixin,
    hook,
)


class Resource(models.IntegerChoices):
    FLAGS = 1
    IDENTITIES = 2
    TRAITS = 3
    ENVIRONMENT_DOCUMENT = 4

    @property
    def is_tracked(self) -> bool:
        return self in {
            self.FLAGS,
            self.IDENTITIES,
            self.TRAITS,
            self.ENVIRONMENT_DOCUMENT,
        }

    @property
    def resource_name(self) -> str:
        return {
            self.FLAGS: "flags",
            self.IDENTITIES: "identities",
            self.TRAITS: "traits",
            self.ENVIRONMENT_DOCUMENT: "environment-document",
        }[self]

    @property
    def column_name(self) -> str | None:
        return {
            self.FLAGS: "flags",
            self.IDENTITIES: "identities",
            self.TRAITS: "traits",
            self.ENVIRONMENT_DOCUMENT: "environment_document",
        }.get(self)

    @classmethod
    def get_from_name(cls, resource_name: str) -> "Resource | None":
        return {
            "flags": cls.FLAGS,
            "identities": cls.IDENTITIES,
            "traits": cls.TRAITS,
            "environment-document": cls.ENVIRONMENT_DOCUMENT,
        }.get(resource_name)


class APIUsageRaw(models.Model):
    environment_id = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    host = models.CharField(max_length=255)
    resource = models.IntegerField(choices=Resource.choices)
    count = models.PositiveIntegerField(default=1)
    labels = HStoreField(default=dict)

    class Meta:
        index_together = (("environment_id", "created_at"),)


class AbstractBucket(LifecycleModelMixin, models.Model):  # type: ignore[misc]
    bucket_size = models.PositiveIntegerField(help_text="Bucket size in minutes")
    created_at = models.DateTimeField()
    total_count = models.PositiveIntegerField()
    environment_id = models.PositiveIntegerField()
    labels = HStoreField(default=dict)

    class Meta:
        abstract = True

    def check_overlapping_buckets(self, filters):  # type: ignore[no-untyped-def]
        overlapping_buckets = self.__class__.objects.filter(
            environment_id=self.environment_id,
            bucket_size=self.bucket_size,
            created_at__gte=self.created_at,
            created_at__lt=self.created_at + timedelta(minutes=self.bucket_size),
            labels__contains=self.labels,
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
    def check_overlapping_buckets(self):  # type: ignore[no-untyped-def]
        filter = models.Q(resource=self.resource)
        super().check_overlapping_buckets(filter)  # type: ignore[no-untyped-call]


class FeatureEvaluationRaw(models.Model):
    feature_name = models.CharField(db_index=True, max_length=2000)
    environment_id = models.PositiveIntegerField()
    evaluation_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    labels = HStoreField(default=dict)

    # Both stored for tracking multivariate split testing.
    identity_identifier = models.CharField(max_length=2000, null=True, default=None)
    enabled_when_evaluated = models.BooleanField(null=True, default=None)

    class Meta:
        indexes = [
            models.Index(
                fields=["created_at"],
                name="f_evaluation_created_at_idx",
            ),
        ]


class FeatureEvaluationBucket(AbstractBucket):
    feature_name = models.CharField(max_length=2000)

    @hook(BEFORE_CREATE)
    def check_overlapping_buckets(self):  # type: ignore[no-untyped-def]
        filter = models.Q(feature_name=self.feature_name)
        super().check_overlapping_buckets(filter)  # type: ignore[no-untyped-call]

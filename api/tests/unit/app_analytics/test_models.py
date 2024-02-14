import pytest
from app_analytics.models import (
    APIUsageBucket,
    FeatureEvaluationBucket,
    Resource,
)
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

if "analytics" not in settings.DATABASES:
    pytest.skip(
        "Skip test if analytics database is not configured", allow_module_level=True
    )


@pytest.mark.django_db(databases=["analytics"])
def test_creating_overlapping_api_usage_bucket_raises_error(db):
    # Given
    created_at = timezone.now()
    bucket_size = 15
    environment_id = 1

    # a bucket
    APIUsageBucket.objects.create(
        resource=Resource.FLAGS,
        bucket_size=bucket_size,
        total_count=10,
        environment_id=environment_id,
        created_at=created_at,
    )

    # When
    with pytest.raises(ValidationError):
        APIUsageBucket.objects.create(
            resource=Resource.FLAGS,
            bucket_size=bucket_size,
            total_count=100,
            environment_id=environment_id,
            created_at=created_at,
        )

    # Then - ValidationError is raised


@pytest.mark.django_db(databases=["analytics"])
def test_creating_overlapping_feature_evaluation_bucket_raises_error(db):
    # Given
    created_at = timezone.now()
    bucket_size = 15
    environment_id = 1
    feature_name = "test-feature"

    # a bucket
    FeatureEvaluationBucket.objects.create(
        feature_name=feature_name,
        bucket_size=bucket_size,
        total_count=10,
        environment_id=environment_id,
        created_at=created_at,
    )

    # When
    with pytest.raises(ValidationError):
        FeatureEvaluationBucket.objects.create(
            feature_name=feature_name,
            bucket_size=bucket_size,
            total_count=100,
            environment_id=environment_id,
            created_at=created_at,
        )

    # Then - ValidationError is raised

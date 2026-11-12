import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from app_analytics.models import (
    APIUsageBucket,
    FeatureEvaluationBucket,
    Resource,
)

pytestmark = pytest.mark.use_analytics_db


def test_api_usage_bucket__overlapping_bucket__raises_validation_error(db):  # type: ignore[no-untyped-def]
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
        labels={"key": "value", "key2": "value2"},
    )

    # When & Then
    with pytest.raises(ValidationError):
        APIUsageBucket.objects.create(
            resource=Resource.FLAGS,
            bucket_size=bucket_size,
            total_count=100,
            environment_id=environment_id,
            created_at=created_at,
            labels={"key": "value"},
        )


def test_feature_evaluation_bucket__overlapping_bucket__raises_validation_error(db):  # type: ignore[no-untyped-def]
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
        labels={"key": "value", "key2": "value2"},
    )

    # When & Then
    with pytest.raises(ValidationError):
        FeatureEvaluationBucket.objects.create(
            feature_name=feature_name,
            bucket_size=bucket_size,
            total_count=100,
            environment_id=environment_id,
            created_at=created_at,
            labels={"key": "value"},
        )

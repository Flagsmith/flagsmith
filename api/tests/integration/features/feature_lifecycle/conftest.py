from collections.abc import Callable
from datetime import timedelta
from typing import Any
from uuid import uuid4

import pytest
from django.utils import timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from app_analytics.constants import ANALYTICS_READ_BUCKET_SIZE
from app_analytics.models import FeatureEvaluationBucket
from features.models import Feature
from projects.code_references.models import ScannedCodeReferences, VCSRepository
from projects.code_references.types import StoredCodeReference, VCSProvider
from projects.tags.models import Tag, TagType

MakeCodeReferencesFixture = Callable[
    [Feature, list[StoredCodeReference]], ScannedCodeReferences
]
MakeFeatureUsageFixture = Callable[[Feature, int], Any]


@pytest.fixture()
def stale_tag(project: int) -> Tag:
    return Tag.objects.create(  # type: ignore[no-any-return]
        project_id=project,
        is_system_tag=True,
        type=TagType.STALE,
    )


@pytest.fixture()
def permanent_tag(project: int) -> Tag:
    return Tag.objects.create(  # type: ignore[no-any-return]
        label="permanent",
        project_id=project,
        is_permanent=True,
        is_system_tag=True,
    )


@pytest.fixture()
def code_references_repository(project: int) -> VCSRepository:
    return VCSRepository.objects.create(
        project_id=project,
        url="https://github.flagsmith.com/core/",
        vcs_provider=VCSProvider.GITHUB,
        last_scanned_at=(timezone.now() - timedelta(days=7)),
    )


@pytest.fixture
def make_code_references(
    code_references_repository: VCSRepository,
) -> MakeCodeReferencesFixture:
    now = timezone.now()
    code_references_repository.last_scanned_at = now
    code_references_repository.save()
    return lambda feature, code_references: ScannedCodeReferences.objects.create(
        created_at=now,
        feature=feature,
        repository=code_references_repository,
        revision=str(uuid4()),
        code_references=code_references,
        code_references_hash="potato",
    )


@pytest.fixture
def make_analytics_db_usage(
    environment: int,
) -> MakeFeatureUsageFixture:
    return lambda feature, evaluation_count: FeatureEvaluationBucket.objects.create(
        feature_name=feature.name,
        bucket_size=15,
        created_at=timezone.now(),
        total_count=evaluation_count,
        environment_id=environment,
    )


@pytest.fixture
def make_influxdb_usage(
    environment: int,
    influxdb: InfluxDBClient,
) -> MakeFeatureUsageFixture:
    write_api = influxdb.write_api(write_options=SYNCHRONOUS)
    return lambda feature, evaluation_count: write_api.write(
        bucket="api_usage_downsampled_15m",
        org="flagsmith",
        record=Point("feature_evaluation")
        .tag("environment_id", str(environment))
        .tag("feature_id", feature.name)
        .field("request_count", evaluation_count)
        .time(timezone.now() - timedelta(minutes=ANALYTICS_READ_BUCKET_SIZE)),
    )

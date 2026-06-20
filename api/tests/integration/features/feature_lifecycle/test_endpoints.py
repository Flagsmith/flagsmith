import freezegun
import pytest
from pytest_django.fixtures import SettingsWrapper
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from features.feature_lifecycle.types import LifecycleStage
from features.models import Feature
from projects.tags.models import Tag
from tests.integration.features.feature_lifecycle.conftest import (
    MakeCodeReferencesFixture,
    MakeFeatureUsageFixture,
)
from users.models import FFAdminUser


@pytest.mark.use_analytics_db
@freezegun.freeze_time("2099-01-01T12:00:00Z")
def test_feature_lifecycle_counts__varied_stages_analytics_db__responds_200_with_json_summary(
    admin_client: APIClient,
    environment: int,
    make_analytics_db_usage: MakeFeatureUsageFixture,
    make_code_references: MakeCodeReferencesFixture,
    permanent_tag: Tag,
    project: int,
    settings: SettingsWrapper,
    stale_tag: Tag,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True

    Feature.objects.create(project_id=project, name="new")

    live_feature = Feature.objects.create(project_id=project, name="live")
    make_code_references(live_feature, [{"file_path": "file.py", "line_number": 1}])

    stale_feature = Feature.objects.create(project_id=project, name="stale")
    make_code_references(stale_feature, [])
    stale_feature.tags.add(stale_tag)

    permanent_feature = Feature.objects.create(project_id=project, name="permanent")
    permanent_feature.tags.add(permanent_tag)

    needs_monitoring_feature = Feature.objects.create(
        project_id=project, name="needs_monitoring"
    )
    needs_monitoring_feature.tags.add(stale_tag)
    make_analytics_db_usage(needs_monitoring_feature, 1)

    to_remove_feature = Feature.objects.create(project_id=project, name="to_remove")
    to_remove_feature.tags.add(stale_tag)

    # When
    response = admin_client.get(
        f"/api/v1/environments/{environment}/feature-lifecycle-counts/"
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        LifecycleStage.NEW: 1,
        LifecycleStage.LIVE: 1,
        LifecycleStage.STALE: 1,
        LifecycleStage.PERMANENT: 1,
        LifecycleStage.NEEDS_MONITORING: 1,
        LifecycleStage.TO_REMOVE: 1,
    }


@pytest.mark.usefixtures("influxdb")
@freezegun.freeze_time("2099-01-01T12:00:00Z")
def test_feature_lifecycle_counts__varied_stages_influxdb__responds_200_with_json_summary(
    admin_client: APIClient,
    environment: int,
    make_code_references: MakeCodeReferencesFixture,
    make_influxdb_usage: MakeFeatureUsageFixture,
    permanent_tag: Tag,
    project: int,
    stale_tag: Tag,
) -> None:
    # Given
    Feature.objects.create(project_id=project, name="new")

    live_feature = Feature.objects.create(project_id=project, name="live")
    make_code_references(live_feature, [{"file_path": "file.py", "line_number": 1}])

    stale_feature = Feature.objects.create(project_id=project, name="stale")
    make_code_references(stale_feature, [])
    stale_feature.tags.add(stale_tag)

    permanent_feature = Feature.objects.create(project_id=project, name="permanent")
    permanent_feature.tags.add(permanent_tag)

    needs_monitoring_feature = Feature.objects.create(
        project_id=project, name="needs_monitoring"
    )
    needs_monitoring_feature.tags.add(stale_tag)
    make_influxdb_usage(needs_monitoring_feature, 1)

    to_remove_feature = Feature.objects.create(project_id=project, name="to_remove")
    to_remove_feature.tags.add(stale_tag)

    # When
    response = admin_client.get(
        f"/api/v1/environments/{environment}/feature-lifecycle-counts/"
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        LifecycleStage.NEW: 1,
        LifecycleStage.LIVE: 1,
        LifecycleStage.STALE: 1,
        LifecycleStage.PERMANENT: 1,
        LifecycleStage.NEEDS_MONITORING: 1,
        LifecycleStage.TO_REMOVE: 1,
    }


def test_feature_lifecycle_counts__no_features__responds_200_with_empty_json_summary(
    admin_client: APIClient,
    environment: int,
    log: StructuredLogCapture,
    organisation: int,
) -> None:
    # Given / When
    response = admin_client.get(
        f"/api/v1/environments/{environment}/feature-lifecycle-counts/"
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {lifecycle_stage: 0 for lifecycle_stage in LifecycleStage}
    assert log.has(
        "summarised",
        level="info",
        organisation__id=organisation,
        environment__id=environment,
    )


def test_feature_lifecycle_counts__anonymous_user__responds_401(
    environment: int,
) -> None:
    # Given
    client = APIClient()

    # When
    response = client.get(
        f"/api/v1/environments/{environment}/feature-lifecycle-counts/"
    )

    # Then
    assert response.status_code == 401


def test_feature_lifecycle_counts__non_member_user__responds_403(
    environment: int,
) -> None:
    # Given
    non_member = FFAdminUser.objects.create(username="who")
    client = APIClient()
    client.force_authenticate(user=non_member)

    # When
    response = client.get(
        f"/api/v1/environments/{environment}/feature-lifecycle-counts/"
    )

    # Then
    assert response.status_code == 403

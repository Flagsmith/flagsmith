from collections.abc import Callable

import freezegun
import pytest
from pytest_django.fixtures import SettingsWrapper
from rest_framework.test import APIClient

from app_analytics.models import FeatureEvaluationBucket
from features.feature_lifecycle.types import LifecycleStage
from features.models import Feature
from projects.code_references.models import ScannedCodeReferences
from projects.tags.models import Tag


@pytest.mark.use_analytics_db
@freezegun.freeze_time("2099-01-01T12:00:00Z")
def test_feature_list_endpoint__varied_stages_analytics_db__responds_200_with_lifecycle_stage_in_each_feature(
    admin_client: APIClient,
    environment: int,
    make_analytics_db_usage: Callable[[Feature, int], FeatureEvaluationBucket],
    make_code_references: Callable[[Feature, list], ScannedCodeReferences],
    permanent_tag: Tag,
    project: int,
    settings: SettingsWrapper,
    stale_tag: Tag,
):
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True

    Feature.objects.create(project_id=project, name="new")

    live_feature = Feature.objects.create(project_id=project, name="live")
    make_code_references(live_feature, [{"file_name": "file.py", "line_number": 1}])

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
    response = admin_client.get(f"/api/v1/projects/{project}/features/?environment={environment}")

    # Then
    assert response.status_code == 200
    json_features = {feature["name"]: feature for feature in response.json()["results"]}
    assert json_features["new"]["lifecycle_stage"] == LifecycleStage.NEW
    assert json_features["live"]["lifecycle_stage"] == LifecycleStage.LIVE
    assert json_features["stale"]["lifecycle_stage"] == LifecycleStage.STALE
    assert json_features["permanent"]["lifecycle_stage"] == LifecycleStage.PERMANENT
    assert json_features["needs_monitoring"]["lifecycle_stage"] == LifecycleStage.STALE
    assert json_features["to_remove"]["lifecycle_stage"] == LifecycleStage.STALE


def test_feature_list_endpoint__varied_stages_influxdb__responds_200_with_lifecycle_stage_in_each_feature():
    raise NotImplementedError


def test_feature_list_endpoint__flag_off__responds_200_with_lifecycle_stage_none():
    raise NotImplementedError


def test_feature_list_endpoint__no_environment__responds_200_with_lifecycle_stage_none():
    raise NotImplementedError


def test_feature_detail_endpoint__new_feature__responds_200_with_lifecycle_stage_new():
    raise NotImplementedError


def test_feature_detail_endpoint__live_feature__responds_200_with_lifecycle_stage_live():
    raise NotImplementedError


def test_feature_detail_endpoint__stale_feature__responds_200_with_lifecycle_stage_stale():
    raise NotImplementedError


def test_feature_detail_endpoint__permanent_feature__responds_200_with_lifecycle_stage_permanent():
    raise NotImplementedError


def test_feature_detail_endpoint__needs_monitoring_feature__responds_200_with_lifecycle_stage_needs_monitoring():
    raise NotImplementedError


def test_feature_detail_endpoint__to_remove_feature__responds_200_with_lifecycle_stage_to_remove():
    raise NotImplementedError


def test_feature_detail_endpoint__flag_off__responds_200_with_lifecycle_stage_none():
    raise NotImplementedError


def test_feature_detail_endpoint__no_environment__responds_200_with_lifecycle_stage_none():
    raise NotImplementedError

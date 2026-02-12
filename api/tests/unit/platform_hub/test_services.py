from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from pytest_mock import MockerFixture

from environments.models import Environment
from features.models import Feature, FeatureState
from organisations.models import (
    Organisation,
    OrganisationSubscriptionInformationCache,
)
from platform_hub import services
from projects.models import Project
from users.models import FFAdminUser


def test_get_summary__empty_orgs__returns_zero_counts(db: None) -> None:
    # Given
    orgs = Organisation.objects.none()

    # When
    result = services.get_summary(orgs)

    # Then
    assert result["total_organisations"] == 0
    assert result["total_flags"] == 0
    assert result["total_users"] == 0
    assert result["total_projects"] == 0
    assert result["total_environments"] == 0
    assert result["total_integrations"] == 0
    assert result["active_organisations"] == 0
    assert result["active_users"] == 0


def test_get_summary__with_data__returns_correct_aggregation(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
    platform_hub_admin_user: FFAdminUser,
) -> None:
    # Given
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_summary(orgs)

    # Then
    assert result["total_organisations"] == 1
    assert result["total_flags"] == 1
    assert result["total_users"] == 1
    assert result["total_projects"] == 1
    assert result["total_environments"] == 1


def test_get_summary__influxdb_backend__uses_get_top_organisations(
    platform_hub_organisation: Organisation,
    platform_hub_admin_user: FFAdminUser,
    mocker: MockerFixture,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False  # type: ignore[attr-defined]
    settings.INFLUXDB_TOKEN = "test-token"  # type: ignore[attr-defined]
    mock_get_top = mocker.patch(
        "platform_hub.services.get_top_organisations",
        return_value={platform_hub_organisation.id: 5000},
    )
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_summary(orgs)

    # Then
    assert result["total_api_calls_30d"] == 5000
    mock_get_top.assert_called_once()


def test_get_summary__postgres_backend__uses_subscription_cache(
    platform_hub_organisation: Organisation,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True  # type: ignore[attr-defined]
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=platform_hub_organisation,
        api_calls_30d=3000,
        allowed_30d_api_calls=10000,
    )
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_summary(orgs)

    # Then
    assert result["total_api_calls_30d"] == 3000


def test_get_summary__no_analytics__returns_zero_api_calls(
    platform_hub_organisation: Organisation,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False  # type: ignore[attr-defined]
    settings.INFLUXDB_TOKEN = ""  # type: ignore[attr-defined]
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_summary(orgs)

    # Then
    assert result["total_api_calls_30d"] == 0


def test_get_organisation_metrics__returns_nested_structure(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False  # type: ignore[attr-defined]
    settings.INFLUXDB_TOKEN = ""  # type: ignore[attr-defined]
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_organisation_metrics(orgs)

    # Then
    assert len(result) == 1
    org_data = result[0]
    assert org_data["id"] == platform_hub_organisation.id
    assert org_data["name"] == "Platform Hub Org"
    assert org_data["total_flags"] == 1
    assert org_data["project_count"] == 1
    assert org_data["environment_count"] == 1
    assert len(org_data["projects"]) == 1
    assert org_data["projects"][0]["name"] == "Hub Project"
    assert len(org_data["projects"][0]["environments"]) == 1


def test_get_organisation_metrics__includes_overage_calculations(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False  # type: ignore[attr-defined]
    settings.INFLUXDB_TOKEN = ""  # type: ignore[attr-defined]
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=platform_hub_organisation,
        api_calls_30d=0,
        allowed_30d_api_calls=1000,
    )
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_organisation_metrics(orgs)

    # Then
    assert len(result) == 1
    org_data = result[0]
    assert org_data["api_calls_allowed"] == 1000
    assert org_data["overage_30d"] == 0
    assert org_data["overage_60d"] == 0
    assert org_data["overage_90d"] == 0


def test_get_organisation_metrics__filters_to_given_orgs(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
    platform_hub_admin_user: FFAdminUser,
    other_organisation: Organisation,
    other_org_project: Project,
    other_org_environment: Environment,
    other_org_feature: Feature,
    settings: pytest.FixtureRequest,
) -> None:
    # Given — only filter to the first org
    settings.USE_POSTGRES_FOR_ANALYTICS = False  # type: ignore[attr-defined]
    settings.INFLUXDB_TOKEN = ""  # type: ignore[attr-defined]
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_organisation_metrics(orgs)

    # Then
    assert len(result) == 1
    assert result[0]["id"] == platform_hub_organisation.id


@pytest.mark.use_analytics_db
def test_get_organisation_metrics__postgres__returns_env_usage(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True  # type: ignore[attr-defined]
    from app_analytics import constants as analytics_constants
    from app_analytics.models import APIUsageBucket, Resource

    yesterday = timezone.now() - timedelta(days=1)
    APIUsageBucket.objects.create(
        environment_id=platform_hub_environment.id,
        resource=Resource.FLAGS,
        total_count=200,
        created_at=yesterday,
        bucket_size=analytics_constants.ANALYTICS_READ_BUCKET_SIZE,
    )
    APIUsageBucket.objects.create(
        environment_id=platform_hub_environment.id,
        resource=Resource.IDENTITIES,
        total_count=100,
        created_at=yesterday,
        bucket_size=analytics_constants.ANALYTICS_READ_BUCKET_SIZE,
    )
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_organisation_metrics(orgs)

    # Then
    assert len(result) == 1
    org_data = result[0]
    assert org_data["api_calls_30d"] > 0
    assert org_data["flag_evaluations_30d"] == 200
    assert org_data["identity_requests_30d"] == 100


def test_get_organisation_metrics__influxdb__returns_org_usage(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_admin_user: FFAdminUser,
    mocker: MockerFixture,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False  # type: ignore[attr-defined]
    settings.INFLUXDB_TOKEN = "test-token"  # type: ignore[attr-defined]
    org_id = platform_hub_organisation.id
    mocker.patch(
        "platform_hub.services.get_top_organisations",
        return_value={org_id: 1000},
    )
    orgs = Organisation.objects.filter(id=org_id)

    # When
    result = services.get_organisation_metrics(orgs)

    # Then
    assert len(result) == 1
    org_data = result[0]
    assert org_data["api_calls_30d"] == 1000


def test_get_organisation_metrics__with_integrations__counts_per_org(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False  # type: ignore[attr-defined]
    settings.INFLUXDB_TOKEN = ""  # type: ignore[attr-defined]
    from integrations.webhook.models import WebhookConfiguration

    WebhookConfiguration.objects.create(
        environment=platform_hub_environment,
        url="https://example.com/webhook",
    )
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_organisation_metrics(orgs)

    # Then
    assert len(result) == 1
    assert result[0]["integration_count"] == 1


def test_get_usage_trends__influxdb__pivots_resources_correctly(
    platform_hub_organisation: Organisation,
    platform_hub_admin_user: FFAdminUser,
    mocker: MockerFixture,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False  # type: ignore[attr-defined]
    settings.INFLUXDB_TOKEN = "test-token"  # type: ignore[attr-defined]
    mocker.patch(
        "app_analytics.influxdb_wrapper.get_platform_usage_trends",
        return_value={
            "2024-01-01": {"flags": 100, "identities": 50, "traits": 10},
            "2024-01-02": {"flags": 200, "identities": 75},
        },
    )
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_usage_trends(orgs, days=30)

    # Then
    assert len(result) == 2
    assert result[0]["date"] == "2024-01-01"
    assert result[0]["api_calls"] == 160  # 100 + 50 + 10
    assert result[0]["flag_evaluations"] == 100
    assert result[0]["identity_requests"] == 50
    assert result[1]["date"] == "2024-01-02"
    assert result[1]["api_calls"] == 275  # 200 + 75
    assert result[1]["flag_evaluations"] == 200
    assert result[1]["identity_requests"] == 75


@pytest.mark.use_analytics_db
def test_get_usage_trends__postgres__pivots_resources_correctly(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True  # type: ignore[attr-defined]
    from app_analytics import constants as analytics_constants
    from app_analytics.models import APIUsageBucket, Resource

    yesterday = timezone.now() - timedelta(days=1)
    APIUsageBucket.objects.create(
        environment_id=platform_hub_environment.id,
        resource=Resource.FLAGS,
        total_count=100,
        created_at=yesterday,
        bucket_size=analytics_constants.ANALYTICS_READ_BUCKET_SIZE,
    )
    APIUsageBucket.objects.create(
        environment_id=platform_hub_environment.id,
        resource=Resource.IDENTITIES,
        total_count=50,
        created_at=yesterday,
        bucket_size=analytics_constants.ANALYTICS_READ_BUCKET_SIZE,
    )
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_usage_trends(orgs, days=30)

    # Then
    assert len(result) >= 1
    day = result[0]
    assert day["flag_evaluations"] == 100
    assert day["identity_requests"] == 50
    assert day["api_calls"] == 150


def test_get_usage_trends__no_analytics__returns_empty(
    platform_hub_organisation: Organisation,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False  # type: ignore[attr-defined]
    settings.INFLUXDB_TOKEN = ""  # type: ignore[attr-defined]
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_usage_trends(orgs, days=30)

    # Then
    assert result == []


def test_get_organisation_metrics__query_count_stable_across_projects(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    """Flag counts use a single batched query, not one per project."""
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False  # type: ignore[attr-defined]
    settings.INFLUXDB_TOKEN = ""  # type: ignore[attr-defined]
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # Measure baseline query count with 1 project.
    with CaptureQueriesContext(connection) as ctx_one:
        services.get_organisation_metrics(orgs)
    baseline = len(ctx_one)

    # Add a second project with its own environment and feature.
    project2 = Project.objects.create(
        name="Second Project",
        organisation=platform_hub_organisation,
    )
    Environment.objects.create(name="Second Env", project=project2)
    Feature.objects.create(name="second_feature", project=project2)

    # When — measure query count with 2 projects.
    with CaptureQueriesContext(connection) as ctx_two:
        result = services.get_organisation_metrics(orgs)

    # Then — query count should not grow per project.
    # The stale flag count still runs one query per project, so we allow
    # exactly +1 for the additional project's stale flag query.
    assert len(ctx_two) <= baseline + 1
    assert len(result) == 1
    assert result[0]["project_count"] == 2


def test_get_stale_flags_per_project__query_count_stable_across_projects(
    platform_hub_organisation: Organisation,
    platform_hub_admin_user: FFAdminUser,
) -> None:
    """Flag counts use a single batched query, not one per project."""
    # Given
    project1 = Project.objects.create(
        name="Project A",
        organisation=platform_hub_organisation,
    )
    Environment.objects.create(name="Env A", project=project1)
    Feature.objects.create(name="feat_a", project=project1)

    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    with CaptureQueriesContext(connection) as ctx_one:
        services.get_stale_flags_per_project(orgs)
    baseline = len(ctx_one)

    # Add a second project.
    project2 = Project.objects.create(
        name="Project B",
        organisation=platform_hub_organisation,
    )
    Environment.objects.create(name="Env B", project=project2)
    Feature.objects.create(name="feat_b", project=project2)

    # When
    with CaptureQueriesContext(connection) as ctx_two:
        result = services.get_stale_flags_per_project(orgs)

    # Then — the flag_counts_by_project query is batched, so only +1
    # for the additional project's stale flag query.
    assert len(ctx_two) <= baseline + 1
    assert len(result) == 2


def test_get_stale_flags_per_project__different_thresholds__counts_correctly(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_admin_user: FFAdminUser,
) -> None:
    # Given — create a feature with a feature state updated long ago
    feature = Feature.objects.create(
        name="stale_feature",
        project=platform_hub_project,
    )
    fs = FeatureState.objects.get(
        feature=feature,
        environment=platform_hub_environment,
    )
    # Make the feature state old
    old_date = timezone.now() - timedelta(days=60)
    FeatureState.objects.filter(id=fs.id).update(updated_at=old_date)

    platform_hub_project.stale_flags_limit_days = 30
    platform_hub_project.save()

    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_stale_flags_per_project(orgs)

    # Then
    assert len(result) == 1
    assert result[0]["project_id"] == platform_hub_project.id
    assert result[0]["stale_flags"] == 1
    assert result[0]["total_flags"] == 1


def test_get_stale_flags_per_project__no_flags__skips_project(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_admin_user: FFAdminUser,
) -> None:
    # Given — project has no features (environment created but no features)
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_stale_flags_per_project(orgs)

    # Then — project with 0 flags should be skipped
    assert result == []


def test_get_stale_flags_per_project__filters_to_given_orgs(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
    other_organisation: Organisation,
    other_org_project: Project,
    other_org_environment: Environment,
    other_org_feature: Feature,
) -> None:
    # Given
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_stale_flags_per_project(orgs)

    # Then
    project_ids = [item["project_id"] for item in result]
    assert other_org_project.id not in project_ids


def test_get_integration_breakdown__counts_all_types_with_scope(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_admin_user: FFAdminUser,
) -> None:
    # Given — create a webhook integration
    from integrations.webhook.models import WebhookConfiguration

    WebhookConfiguration.objects.create(
        environment=platform_hub_environment,
        url="https://example.com/webhook",
    )
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_integration_breakdown(orgs)

    # Then
    webhook_entries = [r for r in result if r["integration_type"] == "webhook"]
    assert len(webhook_entries) == 1
    assert webhook_entries[0]["scope"] == "environment"
    assert webhook_entries[0]["count"] == 1
    assert webhook_entries[0]["organisation_id"] == platform_hub_organisation.id


def test_get_release_pipeline_stats__not_installed__returns_empty(
    platform_hub_organisation: Organisation,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.RELEASE_PIPELINES_LOGIC_INSTALLED = False  # type: ignore[attr-defined]
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_release_pipeline_stats(orgs)

    # Then
    assert result == []


def test_get_release_pipeline_stats__returns_stage_hierarchy(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.RELEASE_PIPELINES_LOGIC_INSTALLED = True  # type: ignore[attr-defined]
    from features.release_pipelines.core.models import (
        PipelineStage,
        PipelineStageAction,
        PipelineStageTrigger,
        ReleasePipeline,
    )

    pipeline = ReleasePipeline.objects.create(
        name="Test Pipeline",
        project=platform_hub_project,
    )
    stage = PipelineStage.objects.create(
        name="Stage 1",
        pipeline=pipeline,
        order=0,
        environment=platform_hub_environment,
    )
    trigger = PipelineStageTrigger.objects.create(
        stage=stage,
        trigger_type="ON_ENTER",
    )
    trigger.trigger_body = {"wait_for": "2 days"}
    trigger.save()
    PipelineStageAction.objects.create(
        stage=stage,
        action_type="TOGGLE_FEATURE",
    )

    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_release_pipeline_stats(orgs)

    # Then
    assert len(result) == 1
    pipeline_data = result[0]
    assert pipeline_data["pipeline_name"] == "Test Pipeline"
    assert pipeline_data["organisation_id"] == platform_hub_organisation.id
    assert pipeline_data["project_id"] == platform_hub_project.id
    assert pipeline_data["is_published"] is False
    assert len(pipeline_data["stages"]) == 1
    stage_data = pipeline_data["stages"][0]
    assert stage_data["stage_name"] == "Stage 1"
    assert stage_data["environment_name"] == "Hub Environment"
    assert stage_data["order"] == 0
    assert stage_data["action_description"] != ""
    assert "2 days" in stage_data["trigger_description"]


def test_get_release_pipeline_stats__stage_without_trigger__returns_empty_description(
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_admin_user: FFAdminUser,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.RELEASE_PIPELINES_LOGIC_INSTALLED = True  # type: ignore[attr-defined]
    from features.release_pipelines.core.models import (
        PipelineStage,
        ReleasePipeline,
    )

    pipeline = ReleasePipeline.objects.create(
        name="No Trigger Pipeline",
        project=platform_hub_project,
    )
    PipelineStage.objects.create(
        name="Stage No Trigger",
        pipeline=pipeline,
        order=0,
        environment=platform_hub_environment,
    )
    orgs = Organisation.objects.filter(id=platform_hub_organisation.id)

    # When
    result = services.get_release_pipeline_stats(orgs)

    # Then
    assert len(result) == 1
    stage_data = result[0]["stages"][0]
    assert stage_data["trigger_description"] == ""
    assert stage_data["action_description"] == ""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

import structlog
from django.conf import settings
from django.db.models import Count, F, QuerySet, Sum
from django.utils import timezone

from app_analytics import constants as analytics_constants
from app_analytics.influxdb_wrapper import get_top_organisations
from app_analytics.models import APIUsageBucket, Resource
from environments.models import Environment
from features.models import Feature
from organisations.models import (
    Organisation,
    OrganisationRole,
    OrganisationSubscriptionInformationCache,
)
from platform_hub.constants import get_integration_registry
from platform_hub.mappers import map_release_pipeline_stage_to_stats_data
from platform_hub.types import (
    EnvironmentMetricsData,
    IntegrationBreakdownData,
    OrganisationMetricsData,
    ProjectMetricsData,
    ReleasePipelineOverviewData,
    ReleasePipelineStageStatsData,
    StaleFlagsPerProjectData,
    SummaryData,
    UsageTrendData,
)
from projects.models import Project
from users.models import FFAdminUser

logger = structlog.get_logger("platform_hub")


def get_summary(
    organisations: QuerySet[Organisation],
    days: int = 30,
) -> SummaryData:
    cutoff = timezone.now() - timedelta(days=days)
    org_ids = set(organisations.values_list("id", flat=True))

    total_flags = Feature.objects.filter(
        project__organisation__in=organisations,
    ).count()

    total_users = (
        FFAdminUser.objects.filter(organisations__in=organisations).distinct().count()
    )

    total_projects = Project.objects.filter(organisation__in=organisations).count()

    total_environments = Environment.objects.filter(
        project__organisation__in=organisations,
    ).count()

    active_users = (
        FFAdminUser.objects.filter(
            organisations__in=organisations,
            last_login__gte=cutoff,
        )
        .distinct()
        .count()
    )

    active_organisations = (
        organisations.filter(users__last_login__gte=cutoff).distinct().count()
    )

    total_integrations = 0
    registry = get_integration_registry()
    for model, org_lookup_path, _ in registry.values():
        total_integrations += model.objects.filter(
            **{f"{org_lookup_path}__in": org_ids},
        ).count()

    total_api_calls_30d = _get_total_api_calls(organisations, org_ids)

    return SummaryData(
        total_organisations=organisations.count(),
        total_flags=total_flags,
        total_users=total_users,
        total_api_calls_30d=total_api_calls_30d,
        active_organisations=active_organisations,
        total_projects=total_projects,
        total_environments=total_environments,
        total_integrations=total_integrations,
        active_users=active_users,
    )


def _get_total_api_calls(
    organisations: QuerySet[Organisation],
    org_ids: set[int],
) -> int:
    if settings.USE_POSTGRES_FOR_ANALYTICS:
        result = OrganisationSubscriptionInformationCache.objects.filter(
            organisation__in=organisations,
        ).aggregate(total=Sum("api_calls_30d"))
        return result["total"] or 0

    if settings.INFLUXDB_TOKEN:
        all_org_usage = get_top_organisations()
        return sum(usage for oid, usage in all_org_usage.items() if oid in org_ids)

    logger.warning("no-analytics-database-configured")
    return 0


def _get_api_usage_for_orgs_influx(
    org_ids: set[int],
    days: int = 30,
) -> dict[int, int]:
    """Get per-org API usage from InfluxDB for the given number of days."""
    date_start = timezone.now() - timedelta(days=days)
    all_org_usage = get_top_organisations(date_start=date_start)
    return {oid: usage for oid, usage in all_org_usage.items() if oid in org_ids}


def _get_api_usage_for_envs_postgres(
    environment_ids: list[int],
    days: int = 30,
) -> dict[int, dict[str, int]]:
    """Get per-environment API usage from Postgres for the given number of days."""
    date_start = timezone.now() - timedelta(days=days)
    qs = (
        APIUsageBucket.objects.filter(
            environment_id__in=environment_ids,
            bucket_size=analytics_constants.ANALYTICS_READ_BUCKET_SIZE,
            created_at__date__gt=date_start.date(),
        )
        .values("environment_id", "resource")
        .annotate(total=Sum("total_count"))
    )
    result: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in qs:
        resource = Resource(row["resource"])
        result[row["environment_id"]][resource.resource_name] = row["total"]
    return result


def _get_env_ids_for_orgs(
    organisations: QuerySet[Organisation],
) -> dict[int, list[int]]:
    """Return a mapping of organisation_id -> list of environment_ids."""
    envs = Environment.objects.filter(
        project__organisation__in=organisations
    ).values_list("id", "project__organisation_id")
    result: dict[int, list[int]] = defaultdict(list)
    for env_id, org_id in envs:
        result[org_id].append(env_id)
    return result


def get_organisation_metrics(
    organisations: QuerySet[Organisation],
) -> list[OrganisationMetricsData]:
    cutoff_30d = timezone.now() - timedelta(days=30)
    org_ids = set(organisations.values_list("id", flat=True))

    orgs = organisations.prefetch_related(
        "projects__environments",
        "users",
    ).order_by("id")

    env_ids_by_org = _get_env_ids_for_orgs(organisations)
    all_env_ids = [eid for eids in env_ids_by_org.values() for eid in eids]

    # API usage data per org (30d/60d/90d)
    org_usage_30d: dict[int, int] = {}
    org_usage_60d: dict[int, int] = {}
    org_usage_90d: dict[int, int] = {}
    env_usage: dict[int, dict[str, int]] = {}

    if settings.USE_POSTGRES_FOR_ANALYTICS:
        env_usage = _get_api_usage_for_envs_postgres(all_env_ids, days=90)
        env_usage_30d = _get_api_usage_for_envs_postgres(all_env_ids, days=30)
        env_usage_60d = _get_api_usage_for_envs_postgres(all_env_ids, days=60)

        for oid, eids in env_ids_by_org.items():
            org_usage_30d[oid] = sum(
                sum(env_usage_30d.get(eid, {}).values()) for eid in eids
            )
            org_usage_60d[oid] = sum(
                sum(env_usage_60d.get(eid, {}).values()) for eid in eids
            )
            org_usage_90d[oid] = sum(
                sum(env_usage.get(eid, {}).values()) for eid in eids
            )
    elif settings.INFLUXDB_TOKEN:
        org_usage_30d = _get_api_usage_for_orgs_influx(org_ids, days=30)
        org_usage_60d = _get_api_usage_for_orgs_influx(org_ids, days=60)
        org_usage_90d = _get_api_usage_for_orgs_influx(org_ids, days=90)
    else:
        logger.warning("no-analytics-database-configured")

    # Allowed API calls per org
    sub_caches = {
        sc.organisation_id: sc
        for sc in OrganisationSubscriptionInformationCache.objects.filter(
            organisation__in=organisations,
        )
    }

    # Flag counts per org
    flag_counts = dict(
        Feature.objects.filter(project__organisation__in=organisations)
        .values("project__organisation_id")
        .annotate(count=Count("id"))
        .values_list("project__organisation_id", "count")
    )

    # Stale flag counts per org
    stale_flag_counts = _get_stale_flag_counts_by_org(organisations)

    # Integration counts per org
    integration_counts = _get_integration_counts_by_org(org_ids)

    # User counts per org
    user_counts = dict(
        FFAdminUser.objects.filter(organisations__in=organisations)
        .values("organisations__id")
        .annotate(count=Count("id", distinct=True))
        .values_list("organisations__id", "count")
    )

    active_user_counts = dict(
        FFAdminUser.objects.filter(
            organisations__in=organisations,
            last_login__gte=cutoff_30d,
        )
        .values("organisations__id")
        .annotate(count=Count("id", distinct=True))
        .values_list("organisations__id", "count")
    )

    admin_user_counts = dict(
        FFAdminUser.objects.filter(
            organisations__in=organisations,
            userorganisation__role=OrganisationRole.ADMIN,
        )
        .values("organisations__id")
        .annotate(count=Count("id", distinct=True))
        .values_list("organisations__id", "count")
    )

    # Per-env usage for nested project/environment data
    per_env_usage_30d: dict[int, dict[str, int]] = {}
    if settings.USE_POSTGRES_FOR_ANALYTICS:
        per_env_usage_30d = _get_api_usage_for_envs_postgres(all_env_ids, days=30)
    elif settings.INFLUXDB_TOKEN:
        # InfluxDB doesn't provide per-environment data easily.
        per_env_usage_30d = {}

    results: list[OrganisationMetricsData] = []
    for org in orgs:
        oid = org.id
        api_calls_30d = org_usage_30d.get(oid, 0)
        api_calls_60d = org_usage_60d.get(oid, 0)
        api_calls_90d = org_usage_90d.get(oid, 0)

        sub_cache = sub_caches.get(oid)
        api_calls_allowed = sub_cache.allowed_30d_api_calls if sub_cache else 0

        overage_30d = max(0, api_calls_30d - api_calls_allowed)
        overage_60d = max(0, api_calls_60d - api_calls_allowed * 2)
        overage_90d = max(0, api_calls_90d - api_calls_allowed * 3)

        total_flags = flag_counts.get(oid, 0)
        stale_flags = stale_flag_counts.get(oid, 0)
        active_flags = total_flags - stale_flags

        # Build per-env usage for flag_evaluations and identity_requests
        org_flag_evals_30d = 0
        org_identity_requests_30d = 0
        org_env_ids = env_ids_by_org.get(oid, [])
        for eid in org_env_ids:
            eu = per_env_usage_30d.get(eid, {})
            org_flag_evals_30d += eu.get("flags", 0)
            org_identity_requests_30d += eu.get("identities", 0)

        projects_data = []
        for project in org.projects.all():
            project_env_ids = [e.id for e in project.environments.all()]
            project_api_calls = sum(
                sum(per_env_usage_30d.get(eid, {}).values()) for eid in project_env_ids
            )
            project_flag_evals = sum(
                per_env_usage_30d.get(eid, {}).get("flags", 0)
                for eid in project_env_ids
            )
            project_flags = Feature.objects.filter(project=project).count()

            envs_data: list[EnvironmentMetricsData] = []
            for env in project.environments.all():
                eu = per_env_usage_30d.get(env.id, {})
                envs_data.append(
                    EnvironmentMetricsData(
                        id=env.id,
                        name=env.name,
                        api_calls_30d=sum(eu.values()),
                        flag_evaluations_30d=eu.get("flags", 0),
                    )
                )

            projects_data.append(
                ProjectMetricsData(
                    id=project.id,
                    name=project.name,
                    api_calls_30d=project_api_calls,
                    flag_evaluations_30d=project_flag_evals,
                    flags=project_flags,
                    environments=envs_data,
                )
            )

        results.append(
            OrganisationMetricsData(
                id=oid,
                name=org.name,
                created_date=org.created_date.isoformat(),
                total_flags=total_flags,
                active_flags=active_flags,
                stale_flags=stale_flags,
                total_users=user_counts.get(oid, 0),
                active_users_30d=active_user_counts.get(oid, 0),
                admin_users=admin_user_counts.get(oid, 0),
                api_calls_30d=api_calls_30d,
                api_calls_60d=api_calls_60d,
                api_calls_90d=api_calls_90d,
                api_calls_allowed=api_calls_allowed,
                flag_evaluations_30d=org_flag_evals_30d,
                identity_requests_30d=org_identity_requests_30d,
                overage_30d=overage_30d,
                overage_60d=overage_60d,
                overage_90d=overage_90d,
                project_count=len(projects_data),
                environment_count=sum(len(p["environments"]) for p in projects_data),
                integration_count=integration_counts.get(oid, 0),
                projects=projects_data,
            )
        )

    return results


def _get_stale_flag_counts_by_org(
    organisations: QuerySet[Organisation],
) -> dict[int, int]:
    """Return a mapping of organisation_id -> stale flag count."""
    projects = Project.objects.filter(
        organisation__in=organisations,
    ).values("id", "organisation_id", "stale_flags_limit_days")

    result: dict[int, int] = defaultdict(int)
    for project in projects:
        cutoff = timezone.now() - timedelta(days=project["stale_flags_limit_days"])

        stale_count = (
            Feature.objects.filter(project_id=project["id"])
            .exclude(
                feature_states__updated_at__gte=cutoff,
            )
            .distinct()
            .count()
        )
        result[project["organisation_id"]] += stale_count

    return result


def _get_integration_counts_by_org(
    org_ids: set[int],
) -> dict[int, int]:
    """Return a mapping of organisation_id -> total integration count."""
    result: dict[int, int] = defaultdict(int)
    registry = get_integration_registry()

    for model, org_lookup_path, _ in registry.values():
        counts = (
            model.objects.filter(**{f"{org_lookup_path}__in": org_ids})
            .values(**{"org_id": F(org_lookup_path)})
            .annotate(count=Count("id"))
        )
        for row in counts:
            result[row["org_id"]] += row["count"]

    return result


def get_usage_trends(
    organisations: QuerySet[Organisation],
    days: int = 30,
) -> list[UsageTrendData]:
    org_ids = set(organisations.values_list("id", flat=True))
    date_start = timezone.now() - timedelta(days=days)

    if settings.USE_POSTGRES_FOR_ANALYTICS:
        return _get_usage_trends_postgres(organisations, date_start)

    if settings.INFLUXDB_TOKEN:
        return _get_usage_trends_influx(org_ids, date_start)

    logger.warning("no-analytics-database-configured")
    return []


def _get_usage_trends_postgres(
    organisations: QuerySet[Organisation],
    date_start: object,
) -> list[UsageTrendData]:
    env_ids = list(
        Environment.objects.filter(
            project__organisation__in=organisations,
        ).values_list("id", flat=True)
    )

    qs = (
        APIUsageBucket.objects.filter(
            environment_id__in=env_ids,
            bucket_size=analytics_constants.ANALYTICS_READ_BUCKET_SIZE,
            created_at__date__gt=date_start,
        )
        .values("created_at__date", "resource")
        .annotate(total=Sum("total_count"))
        .order_by("created_at__date")
    )

    daily: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in qs:
        date_str = row["created_at__date"].isoformat()
        resource = Resource(row["resource"])
        daily[date_str][resource.resource_name] = row["total"]

    results: list[UsageTrendData] = []
    for date_str in sorted(daily.keys()):
        data = daily[date_str]
        results.append(
            UsageTrendData(
                date=date_str,
                api_calls=sum(data.values()),
                flag_evaluations=data.get("flags", 0),
                identity_requests=data.get("identities", 0),
            )
        )

    return results


def _get_usage_trends_influx(
    org_ids: set[int],
    date_start: object,
) -> list[UsageTrendData]:
    from app_analytics.influxdb_wrapper import get_platform_usage_trends

    raw = get_platform_usage_trends(
        date_start=date_start,  # type: ignore[arg-type]
        date_stop=timezone.now(),
        organisation_ids=list(org_ids),
    )

    results: list[UsageTrendData] = []
    for date_str in sorted(raw.keys()):
        data = raw[date_str]
        results.append(
            UsageTrendData(
                date=date_str,
                api_calls=sum(data.values()),
                flag_evaluations=data.get("flags", 0),
                identity_requests=data.get("identities", 0),
            )
        )

    return results


def get_stale_flags_per_project(
    organisations: QuerySet[Organisation],
) -> list[StaleFlagsPerProjectData]:
    projects = (
        Project.objects.filter(organisation__in=organisations)
        .select_related("organisation")
        .order_by("organisation__name", "name")
    )

    results: list[StaleFlagsPerProjectData] = []
    for project in projects:
        total_flags = Feature.objects.filter(project=project).count()
        if total_flags == 0:
            continue

        cutoff = timezone.now() - timedelta(days=project.stale_flags_limit_days)
        stale_flags = (
            Feature.objects.filter(project=project)
            .exclude(feature_states__updated_at__gte=cutoff)
            .distinct()
            .count()
        )

        results.append(
            StaleFlagsPerProjectData(
                organisation_id=project.organisation_id,
                organisation_name=project.organisation.name,
                project_id=project.id,
                project_name=project.name,
                stale_flags=stale_flags,
                total_flags=total_flags,
            )
        )

    return results


def get_integration_breakdown(
    organisations: QuerySet[Organisation],
) -> list[IntegrationBreakdownData]:
    org_ids = set(organisations.values_list("id", flat=True))
    org_names = dict(organisations.values_list("id", "name"))
    registry = get_integration_registry()

    results: list[IntegrationBreakdownData] = []
    for key, (model, org_lookup_path, scope) in registry.items():
        counts = (
            model.objects.filter(**{f"{org_lookup_path}__in": org_ids})
            .values(**{"org_id": F(org_lookup_path)})
            .annotate(count=Count("id"))
        )
        for row in counts:
            oid = row["org_id"]
            results.append(
                IntegrationBreakdownData(
                    organisation_id=oid,
                    organisation_name=org_names.get(oid, ""),
                    integration_type=key,
                    scope=scope,
                    count=row["count"],
                )
            )

    return results


def get_release_pipeline_stats(
    organisations: QuerySet[Organisation],
) -> list[ReleasePipelineOverviewData]:
    if not settings.RELEASE_PIPELINES_LOGIC_INSTALLED:
        return []

    from features.release_pipelines.core.models import (
        PipelineStage,
        ReleasePipeline,
    )

    pipelines = (
        ReleasePipeline.objects.filter(
            project__organisation__in=organisations,
        )
        .select_related("project__organisation")
        .prefetch_related(
            "stages__environment",
            "stages__trigger",
            "stages__actions",
        )
        .order_by("project__organisation__name", "project__name", "name")
    )

    results: list[ReleasePipelineOverviewData] = []
    for pipeline in pipelines:
        stages_qs: QuerySet[PipelineStage] = pipeline.stages.order_by("order")

        total_features = pipeline.get_feature_versions_in_pipeline_qs().count()
        last_stage = pipeline.get_last_stage()
        completed_features = (
            last_stage.get_completed_feature_versions_qs().count() if last_stage else 0
        )
        total_features += completed_features

        stages_data: list[ReleasePipelineStageStatsData] = [
            map_release_pipeline_stage_to_stats_data(stage) for stage in stages_qs
        ]

        results.append(
            ReleasePipelineOverviewData(
                organisation_id=pipeline.project.organisation_id,
                organisation_name=pipeline.project.organisation.name,
                project_id=pipeline.project_id,
                project_name=pipeline.project.name,
                pipeline_id=pipeline.id,
                pipeline_name=pipeline.name,
                is_published=pipeline.published_at is not None,
                total_features=total_features,
                completed_features=completed_features,
                stages=stages_data,
            )
        )

    return results

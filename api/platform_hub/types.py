from typing import TypedDict


class SummaryData(TypedDict):
    total_organisations: int
    total_flags: int
    total_users: int
    total_api_calls_30d: int
    active_organisations: int
    total_projects: int
    total_environments: int
    total_integrations: int
    active_users: int


class EnvironmentMetricsData(TypedDict):
    id: int
    name: str
    api_calls_30d: int
    flag_evaluations_30d: int


class ProjectMetricsData(TypedDict):
    id: int
    name: str
    api_calls_30d: int
    flag_evaluations_30d: int
    flags: int
    environments: list[EnvironmentMetricsData]


class OrganisationMetricsData(TypedDict):
    id: int
    name: str
    created_date: str
    total_flags: int
    active_flags: int
    stale_flags: int
    total_users: int
    active_users_30d: int
    admin_users: int
    api_calls_30d: int
    api_calls_60d: int
    api_calls_90d: int
    api_calls_allowed: int
    flag_evaluations_30d: int
    identity_requests_30d: int
    overage_30d: int
    overage_60d: int
    overage_90d: int
    project_count: int
    environment_count: int
    integration_count: int
    projects: list[ProjectMetricsData]


class UsageTrendData(TypedDict):
    date: str
    api_calls: int
    flag_evaluations: int
    identity_requests: int


class StaleFlagsPerProjectData(TypedDict):
    organisation_id: int
    organisation_name: str
    project_id: int
    project_name: str
    stale_flags: int
    total_flags: int


class IntegrationBreakdownData(TypedDict):
    organisation_id: int
    organisation_name: str
    integration_type: str
    scope: str
    count: int


class ReleasePipelineStageStatsData(TypedDict):
    stage_name: str
    environment_name: str
    order: int
    features_in_stage: int
    features_completed: int
    action_description: str
    trigger_description: str


class ReleasePipelineOverviewData(TypedDict):
    organisation_id: int
    organisation_name: str
    project_id: int
    project_name: str
    pipeline_id: int
    pipeline_name: str
    is_published: bool
    total_features: int
    completed_features: int
    stages: list[ReleasePipelineStageStatsData]

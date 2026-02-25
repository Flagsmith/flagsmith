from rest_framework import serializers


class DaysQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    days = serializers.ChoiceField(
        choices=[30, 60, 90],
        default=30,
    )

    def validate_days(self, value: str | int) -> int:
        return int(value)


class SummarySerializer(serializers.Serializer):  # type: ignore[type-arg]
    total_organisations = serializers.IntegerField()
    total_flags = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_api_calls_30d = serializers.IntegerField()
    active_organisations = serializers.IntegerField()
    total_projects = serializers.IntegerField()
    total_environments = serializers.IntegerField()
    total_integrations = serializers.IntegerField()
    active_users = serializers.IntegerField()


class EnvironmentMetricsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    id = serializers.IntegerField()
    name = serializers.CharField()
    api_calls_30d = serializers.IntegerField()
    flag_evaluations_30d = serializers.IntegerField()


class ProjectMetricsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    id = serializers.IntegerField()
    name = serializers.CharField()
    api_calls_30d = serializers.IntegerField()
    flag_evaluations_30d = serializers.IntegerField()
    flags = serializers.IntegerField()
    environments = EnvironmentMetricsSerializer(many=True)


class OrganisationMetricsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    id = serializers.IntegerField()
    name = serializers.CharField()
    created_date = serializers.CharField()
    total_flags = serializers.IntegerField()
    active_flags = serializers.IntegerField()
    stale_flags = serializers.IntegerField()
    total_users = serializers.IntegerField()
    active_users_30d = serializers.IntegerField()
    admin_users = serializers.IntegerField()
    api_calls_30d = serializers.IntegerField()
    api_calls_60d = serializers.IntegerField()
    api_calls_90d = serializers.IntegerField()
    api_calls_allowed = serializers.IntegerField()
    flag_evaluations_30d = serializers.IntegerField()
    identity_requests_30d = serializers.IntegerField()
    overage_30d = serializers.IntegerField()
    overage_60d = serializers.IntegerField()
    overage_90d = serializers.IntegerField()
    project_count = serializers.IntegerField()
    environment_count = serializers.IntegerField()
    integration_count = serializers.IntegerField()
    projects = ProjectMetricsSerializer(many=True)


class UsageTrendSerializer(serializers.Serializer):  # type: ignore[type-arg]
    date = serializers.CharField()
    api_calls = serializers.IntegerField()
    flag_evaluations = serializers.IntegerField()
    identity_requests = serializers.IntegerField()


class StaleFlagsPerProjectSerializer(serializers.Serializer):  # type: ignore[type-arg]
    organisation_id = serializers.IntegerField()
    organisation_name = serializers.CharField()
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    stale_flags = serializers.IntegerField()
    total_flags = serializers.IntegerField()


class IntegrationBreakdownSerializer(serializers.Serializer):  # type: ignore[type-arg]
    organisation_id = serializers.IntegerField()
    organisation_name = serializers.CharField()
    integration_type = serializers.CharField()
    scope = serializers.CharField()
    count = serializers.IntegerField()


class ReleasePipelineStageStatsSerializer(
    serializers.Serializer,  # type: ignore[type-arg]
):
    stage_name = serializers.CharField()
    environment_name = serializers.CharField()
    order = serializers.IntegerField()
    features_in_stage = serializers.IntegerField()
    features_completed = serializers.IntegerField()
    action_description = serializers.CharField()
    trigger_description = serializers.CharField()


class ReleasePipelineOverviewSerializer(serializers.Serializer):  # type: ignore[type-arg]
    organisation_id = serializers.IntegerField()
    organisation_name = serializers.CharField()
    project_id = serializers.IntegerField()
    project_name = serializers.CharField()
    pipeline_id = serializers.IntegerField()
    pipeline_name = serializers.CharField()
    is_published = serializers.BooleanField()
    total_features = serializers.IntegerField()
    completed_features = serializers.IntegerField()
    stages = ReleasePipelineStageStatsSerializer(many=True)

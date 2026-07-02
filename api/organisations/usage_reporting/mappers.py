import base64
from datetime import timedelta

from common.core.utils import get_version
from django.utils import timezone

from app_analytics.analytics_db_service import get_usage_data_for_window
from app_analytics.dataclasses import UsageData
from organisations.models import Organisation
from organisations.usage_reporting.dataclasses import (
    ApiCallBreakdown,
    ProjectUsage,
    UsageSnapshot,
)

# The Control Plane rejects payloads with more than this many project_usage rows.
MAX_PROJECT_USAGE_ROWS = 5_000


def map_signature_to_control_plane_auth_token(signature_b64: str) -> str:
    raw_signature = base64.b64decode(signature_b64)
    return base64.urlsafe_b64encode(raw_signature).decode("ascii").rstrip("=")


def map_usage_data_to_total_api_calls(usage_data: list[UsageData]) -> int:
    return sum(
        data.flags + data.identities + data.traits + data.environment_document
        for data in usage_data
    )


def map_usage_data_to_api_call_breakdown(
    usage_data: list[UsageData],
) -> ApiCallBreakdown:
    return ApiCallBreakdown(
        flags=sum(data.flags for data in usage_data),
        identities=sum(data.identities for data in usage_data),
        traits=sum(data.traits for data in usage_data),
        environment_documents=sum(data.environment_document for data in usage_data),
    )


def map_project_usage_data_to_project_usage(
    usage_data_by_project_id: dict[int, list[UsageData]],
) -> list[ProjectUsage]:
    rows = [
        ProjectUsage(
            project_id=project_id,
            api_call_count=map_usage_data_to_total_api_calls(usage_data),
        )
        for project_id, usage_data in usage_data_by_project_id.items()
    ]
    # Highest usage first
    rows.sort(key=lambda row: row.api_call_count, reverse=True)
    return rows[:MAX_PROJECT_USAGE_ROWS]


def map_organisation_to_usage_snapshot(organisation: Organisation) -> UsageSnapshot:
    hour_end = timezone.now().replace(minute=0, second=0, microsecond=0)
    hour_start = hour_end - timedelta(hours=1)
    seat_count = organisation.num_seats
    instance_version = get_version()
    usage_data = get_usage_data_for_window(organisation, hour_start, hour_end)
    usage_data_by_project_id = {
        project.id: get_usage_data_for_window(
            organisation, hour_start, hour_end, project_id=project.id
        )
        for project in organisation.projects.all()
    }

    # No data access past this point!

    return UsageSnapshot(
        timestamp=hour_start,
        seat_count=seat_count,
        api_call_total=map_usage_data_to_total_api_calls(usage_data),
        api_call_breakdown=map_usage_data_to_api_call_breakdown(usage_data),
        project_count=len(usage_data_by_project_id),
        instance_version=instance_version,
        project_usage=map_project_usage_data_to_project_usage(usage_data_by_project_id),
    )

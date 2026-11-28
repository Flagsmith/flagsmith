from datetime import timedelta

import structlog
from common.core.utils import get_version
from django.conf import settings
from django.utils import timezone

from app_analytics.analytics_db_service import get_usage_data_for_window
from app_analytics.dataclasses import UsageData
from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation
from projects.models import Project
from telemetry.control_plane.client import post_usage_snapshot
from telemetry.dataclasses import ApiCallBreakdown, ProjectUsage, UsageSnapshot
from telemetry.types import ResolvedTelemetryAttributes

logger = structlog.get_logger("usage_reporting")

MAX_PROJECT_USAGE_ROWS = 5_000


def push_usage_snapshots() -> None:
    if not (settings.ENABLE_TELEMETRY):
        logger.debug("run.skipped", reason="telemetry_disabled")
        return
    if not (base_url := settings.CONTROL_PLANE_URL):
        logger.debug("run.skipped", reason="control_plane_url_unset")
        return
    if not (organisations := _get_licensed_organisations()):
        logger.debug("run.skipped", reason="no_licensed_organisations")
        return

    for organisation in organisations:
        with structlog.contextvars.bound_contextvars(organisation__id=organisation.id):
            try:
                post_usage_snapshot(
                    base_url=base_url,
                    snapshot=_get_usage_snapshot(organisation),
                    signature_b64=organisation.licence.signature,
                )
            except Exception:
                logger.exception("snapshot.errored")


def _get_licensed_organisations() -> list[Organisation]:
    if settings.LICENSING_INSTALLED:  # pragma: no cover
        return list(
            Organisation.objects.filter(licence__isnull=False).select_related("licence")
        )
    return []


def _sum_api_calls(usage_data: list[UsageData]) -> int:
    return sum(
        data.flags + data.identities + data.traits + data.environment_document
        for data in usage_data
    )


def _map_to_top_project_usage(
    usage_data_by_project_id: dict[int, list[UsageData]],
) -> list[ProjectUsage]:
    rows = [
        ProjectUsage(
            project_id=project_id,
            api_call_count=_sum_api_calls(usage_data),
        )
        for project_id, usage_data in usage_data_by_project_id.items()
    ]
    # Highest usage first
    rows.sort(key=lambda row: row.api_call_count, reverse=True)
    return rows[:MAX_PROJECT_USAGE_ROWS]


def _map_to_api_call_breakdown(
    usage_data: list[UsageData],
) -> ApiCallBreakdown:
    return ApiCallBreakdown(
        flags=sum(data.flags for data in usage_data),
        identities=sum(data.identities for data in usage_data),
        traits=sum(data.traits for data in usage_data),
        environment_documents=sum(data.environment_document for data in usage_data),
    )


def _get_usage_snapshot(organisation: Organisation) -> UsageSnapshot:
    hour_end = timezone.now().replace(minute=0, second=0, microsecond=0)
    hour_start = hour_end - timedelta(hours=24)
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
        api_call_total=_sum_api_calls(usage_data),
        api_call_breakdown=_map_to_api_call_breakdown(usage_data),
        project_count=len(usage_data_by_project_id),
        instance_version=instance_version,
        project_usage=_map_to_top_project_usage(usage_data_by_project_id),
    )


def get_resolved_telemetry_attributes(
    ids: ResolvedTelemetryAttributes,
) -> ResolvedTelemetryAttributes:
    """
    Resolve as many keys in `ids` as possible from the database.

    Makes at most one query, from the most specific key present.
    """
    resolved_ids = ids.copy()

    if "environment__id" not in resolved_ids and (
        environment_api_key := resolved_ids.get("environment__key")
    ):
        if environment_ids := (
            Environment.objects.filter(api_key=environment_api_key)
            .values_list("id", "project_id", "project__organisation_id")
            .first()
        ):
            (
                resolved_ids["environment__id"],
                resolved_ids["project__id"],
                resolved_ids["organisation__id"],
            ) = environment_ids
        return resolved_ids

    if "project__id" not in resolved_ids and "feature__id" in resolved_ids:
        if feature_ids := (
            Feature.objects.filter(id=resolved_ids["feature__id"])
            .values_list("project_id", "project__organisation_id")
            .first()
        ):
            (
                resolved_ids["project__id"],
                resolved_ids["organisation__id"],
            ) = feature_ids
        return resolved_ids

    if "organisation__id" not in resolved_ids and "project__id" in resolved_ids:
        if (
            organisation_id := Project.objects.filter(pk=resolved_ids["project__id"])
            .values_list("organisation_id", flat=True)
            .first()
        ) is not None:
            resolved_ids["organisation__id"] = organisation_id

    return resolved_ids

from environments.models import Environment
from features.models import Feature
from projects.models import Project
from telemetry.types import ResolvedIds


def get_resolved_ids(ids: ResolvedIds) -> ResolvedIds:
    """
    Resolve as many keys in `ids` as possible from the database.

    Makes at most one query, from the most specific key present.
    """
    resolved_ids = ids.copy()

    if "environment__id" not in resolved_ids and (
        environment_api_key := resolved_ids.get("environment__api_key")
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

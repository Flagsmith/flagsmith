import typing

from telemetry.types import ResolvedTelemetryAttributes


def map_view_kwargs_to_telemetry_attributes(
    view_kwargs: dict[str, typing.Any],
) -> ResolvedTelemetryAttributes:
    """Map the URL kwargs of a view to the IDs of the entities it acts on."""
    ids: ResolvedTelemetryAttributes = {}
    if str(organisation_pk := view_kwargs.get("organisation_pk", "")).isdecimal():
        ids["organisation__id"] = int(organisation_pk)
    if str(project_pk := view_kwargs.get("project_pk", "")).isdecimal():
        ids["project__id"] = int(project_pk)
    if str(feature_pk := view_kwargs.get("feature_pk", "")).isdecimal():
        ids["feature__id"] = int(feature_pk)
    if environment_api_key := view_kwargs.get("environment_api_key"):
        ids["environment__key"] = environment_api_key
    return ids

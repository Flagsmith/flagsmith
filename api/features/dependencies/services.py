import typing
from collections import defaultdict

import jsonpath_rfc9535
import structlog
from jsonpath_rfc9535.exceptions import JSONPathError
from jsonpath_rfc9535.segments import JSONPathChildSegment, JSONPathSegment
from jsonpath_rfc9535.selectors import NameSelector

from features.dependencies.exceptions import (
    CircularDependencyError,
    PrerequisiteFeatureNotFoundError,
)
from features.dependencies.models import SegmentFlagReference
from features.dependencies.types import DependencyEdge, DependencyPath
from features.models import Feature, FeatureSegment
from segments.services import get_overrides_in_effect
from segments.types import SegmentRule

if typing.TYPE_CHECKING:
    from segments.models import Segment

logger = structlog.get_logger("features")

JSONPathStr = str


def index_segment_flag_references(segment: "Segment") -> None:
    """Materialise the segment's `$.flags` conditions as SegmentFlagReference rows."""
    feature_names_by_json_path = {
        f"{rule_json_path}.conditions[{condition_index}]": feature_name
        for rule_json_path, rule in _get_rules_by_json_path(
            segment.rules_data or []
        ).items()
        for condition_index, condition in enumerate(rule["conditions"])
        if (condition_property := condition["property"])
        and (feature_name := _get_prerequisite_feature_name(condition_property))
    }
    feature_ids_by_name = dict(
        Feature.objects.filter(
            project_id=segment.project_id,
            name__in=set(feature_names_by_json_path.values()),
        ).values_list("name", "id")
    )
    for condition_json_path, feature_name in feature_names_by_json_path.items():
        if feature_name not in feature_ids_by_name:
            raise PrerequisiteFeatureNotFoundError(
                prerequisite_feature=feature_name,
                condition_json_path=condition_json_path,
            )
    references = SegmentFlagReference.objects.filter(segment=segment)
    previous_feature_names = set(
        references.values_list("prerequisite_feature__name", flat=True)
    )
    references.delete()
    SegmentFlagReference.objects.bulk_create(
        SegmentFlagReference(
            segment=segment,
            prerequisite_feature_id=feature_ids_by_name[feature_name],
            condition_json_path=condition_json_path,
        )
        for condition_json_path, feature_name in feature_names_by_json_path.items()
    )
    overrides = FeatureSegment.objects.filter(segment=segment).select_related(
        "environment", "feature"
    )
    for feature_name in previous_feature_names - feature_ids_by_name.keys():
        for override in overrides:
            logger.info(
                "dependencies.deleted",
                organisation__id=segment.project.organisation_id,
                project__id=segment.project_id,
                environment__key=override.environment.api_key,
                feature__name=override.feature.name,
                prerequisite_feature__name=feature_name,
            )
    for feature_name in feature_ids_by_name.keys() - previous_feature_names:
        for override in overrides:
            logger.info(
                "dependencies.created",
                organisation__id=segment.project.organisation_id,
                project__id=segment.project_id,
                environment__key=override.environment.api_key,
                feature__name=override.feature.name,
                prerequisite_feature__name=feature_name,
            )


def delete_segment_flag_references(segment: "Segment") -> None:
    """Drop the segment's index rows, reporting every dependency lost."""
    references = SegmentFlagReference.objects.filter(segment=segment).select_related(
        "prerequisite_feature"
    )
    overrides = FeatureSegment.objects.filter(segment=segment).select_related(
        "environment", "feature"
    )
    for override in overrides:
        for reference in references:
            logger.info(
                "dependencies.deleted",
                organisation__id=segment.project.organisation_id,
                project__id=segment.project_id,
                environment__key=override.environment.api_key,
                feature__name=override.feature.name,
                prerequisite_feature__name=reference.prerequisite_feature.name,
            )
    references.delete()


def validate_segment_flag_dependencies(segment: "Segment") -> None:
    """Raise if any feature the segment overrides ends up depending on itself."""
    for override in (
        get_overrides_in_effect()
        .filter(segment=segment)
        .select_related("environment", "feature")
    ):
        edges: dict[str, list[DependencyEdge]] = defaultdict(list)
        for (
            feature_name,
            prerequisite_feature_name,
            segment_id,
            segment_name,
            condition_json_path,
        ) in (
            get_overrides_in_effect()
            .filter(
                environment=override.environment,
                segment__flag_references__isnull=False,
            )
            .values_list(
                "feature__name",
                "segment__flag_references__prerequisite_feature__name",
                "segment_id",
                "segment__name",
                "segment__flag_references__condition_json_path",
            )
        ):
            edges[feature_name].append(
                {
                    "feature": feature_name,
                    "needs": prerequisite_feature_name,
                    "segment": {
                        "id": segment_id,
                        "name": segment_name,
                        "condition_json_path": condition_json_path,
                    },
                }
            )
        pending: list[DependencyPath] = [
            [edge] for edge in edges[override.feature.name]
        ]
        visited: set[str] = set()
        while pending:
            path = pending.pop()
            if (prerequisite_feature_name := path[-1]["needs"]) in visited:
                continue
            if prerequisite_feature_name == override.feature.name:
                logger.info(
                    "dependencies.create_failed",
                    organisation__id=segment.project.organisation_id,
                    project__id=segment.project_id,
                    environment__key=override.environment.api_key,
                    feature__name=override.feature.name,
                    prerequisite_feature__name=path[0]["needs"],
                )
                raise CircularDependencyError(path=path)
            visited.add(prerequisite_feature_name)
            pending += [[*path, edge] for edge in edges[prerequisite_feature_name]]


def _get_rules_by_json_path(
    rules: list[SegmentRule],
) -> dict[JSONPathStr, SegmentRule]:
    rules_by_json_path: dict[JSONPathStr, SegmentRule] = {}
    for rule_index, rule in enumerate(rules):
        rule_json_path = f"$[{rule_index}]"
        rules_by_json_path[rule_json_path] = rule
        for nested_index, nested_rule in enumerate(rule.get("rules", [])):
            rules_by_json_path[f"{rule_json_path}.rules[{nested_index}]"] = nested_rule
    return rules_by_json_path


def _get_prerequisite_feature_name(condition_property: str) -> str | None:
    """Return the feature name a `$.flags.<feature>` condition points at, if it does."""
    # Because of historical decisions, `$['flags']` can be a trait.
    if not condition_property.startswith("$.flags"):
        return None
    try:
        query_segments = jsonpath_rfc9535.compile(condition_property).segments
    except JSONPathError:
        return None
    if len(query_segments) < 2 or _get_selected_name(query_segments[0]) != "flags":
        return None
    return _get_selected_name(query_segments[1])


def _get_selected_name(query_segment: JSONPathSegment) -> str | None:
    if (
        not isinstance(query_segment, JSONPathChildSegment)
        or len(query_segment.selectors) != 1
    ):
        return None
    selector = query_segment.selectors[0]
    return selector.name if isinstance(selector, NameSelector) else None

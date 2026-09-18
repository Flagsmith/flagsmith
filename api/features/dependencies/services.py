import typing
from collections import defaultdict
from collections.abc import Collection

import structlog

from environments.models import Environment
from features.dependencies.exceptions import (
    CircularDependencyError,
    PrerequisiteFeatureNotFoundError,
)
from features.dependencies.mappers import map_rules_to_prerequisite_feature_names
from features.dependencies.models import SegmentFlagReference
from features.dependencies.types import DependencyEdge, DependencyPath, FeatureName
from features.models import Feature, FeatureSegment
from segments.services import get_overrides_in_effect

if typing.TYPE_CHECKING:
    from segments.models import Segment

logger = structlog.get_logger("features")


def index_segment_flag_references(segment: "Segment") -> None:
    """Materialise the segment's `$.flags` conditions as SegmentFlagReference rows."""
    feature_names_by_json_path = map_rules_to_prerequisite_feature_names(
        segment.rules_data or []
    )
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
    for override in FeatureSegment.objects.filter(segment=segment).select_related(
        "environment__project", "feature"
    ):
        report_flag_dependencies(
            environment=override.environment,
            feature=override.feature,
            created=feature_ids_by_name.keys() - previous_feature_names,
            deleted=previous_feature_names - feature_ids_by_name.keys(),
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


def report_flag_dependencies(
    *,
    environment: Environment,
    feature: Feature,
    created: Collection[FeatureName],
    deleted: Collection[FeatureName],
) -> None:
    """Report the prerequisites a feature gains and loses in an environment."""
    log = logger.bind(
        organisation__id=environment.project.organisation_id,
        project__id=environment.project_id,
        environment__key=environment.api_key,
        feature__name=feature.name,
    )
    for feature_name in deleted:
        log.info("dependencies.deleted", prerequisite_feature__name=feature_name)
    for feature_name in created:
        log.info("dependencies.created", prerequisite_feature__name=feature_name)


def validate_segment_flag_dependencies(segment: "Segment") -> None:
    """Raise if any feature the segment overrides ends up depending on itself."""
    edges_by_environment_id: dict[int, dict[FeatureName, list[DependencyEdge]]] = {}
    for override in (
        get_overrides_in_effect()
        .filter(segment=segment)
        .select_related("environment", "feature")
    ):
        if override.environment_id not in edges_by_environment_id:
            edges_by_environment_id[override.environment_id] = _get_dependency_edges(
                override.environment
            )
        edges = edges_by_environment_id[override.environment_id]
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
                raise CircularDependencyError(
                    environment={
                        "key": override.environment.api_key,
                        "name": override.environment.name,
                    },
                    path=path,
                )
            visited.add(prerequisite_feature_name)
            pending += [[*path, edge] for edge in edges[prerequisite_feature_name]]


def _get_dependency_edges(
    environment: Environment,
) -> dict[FeatureName, list[DependencyEdge]]:
    edges: dict[FeatureName, list[DependencyEdge]] = defaultdict(list)
    for (
        feature_name,
        prerequisite_feature_name,
        segment_id,
        segment_name,
        condition_json_path,
    ) in (
        get_overrides_in_effect()
        .filter(
            environment=environment,
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
    return edges

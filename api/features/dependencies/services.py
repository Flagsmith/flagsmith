import json
from collections import defaultdict
from collections.abc import Collection

import structlog
from django.db import transaction
from flag_engine.segments import constants
from ordered_model.models import OrderedModelQuerySet  # type: ignore[import-untyped]

from api_keys.user import APIKeyUser
from audit.constants import FEATURE_DEPENDENCY_CREATED_MESSAGE
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from features.dependencies.exceptions import (
    CircularDependencyError,
    DependencyExistsError,
    FeatureIsPrerequisiteError,
    PrerequisiteFeatureNotFoundError,
    PrerequisiteHasPrerequisiteError,
    PrerequisiteIsSelfError,
)
from features.dependencies.mappers import (
    map_reference_to_dependency_edge,
    map_rules_to_prerequisite_feature_names,
)
from features.dependencies.models import SegmentFlagReference
from features.dependencies.types import (
    DependencyEdge,
    DependencyList,
    DependencyPath,
    FeatureName,
    ReferencingEnvironment,
)
from features.models import Feature, FeatureSegment
from segments.models import Segment
from segments.services import (
    get_all_live_or_scheduled_overrides,
    write_segment_rules,
)
from segments.types import SegmentCondition, SegmentRule
from users.models import FFAdminUser

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
    existing_references = SegmentFlagReference.objects.filter(segment=segment)
    if not existing_references.exists():
        return
    edges_by_environment_id: dict[int, dict[FeatureName, list[DependencyEdge]]] = {}
    for override in (
        get_all_live_or_scheduled_overrides()
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
            if (
                prerequisite_feature_name := path[-1]["prerequisite"]["name"]
            ) in visited:
                continue
            if prerequisite_feature_name == override.feature.name:
                logger.info(
                    "dependencies.create_failed",
                    organisation__id=segment.project.organisation_id,
                    project__id=segment.project_id,
                    environment__key=override.environment.api_key,
                    feature__name=override.feature.name,
                    prerequisite_feature__name=path[0]["prerequisite"]["name"],
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
        feature_id,
        feature_name,
        prerequisite_feature_id,
        prerequisite_feature_name,
        segment_id,
        segment_name,
        segment_rules,
        condition_json_path,
        is_system_segment,
    ) in (
        get_all_live_or_scheduled_overrides()
        .filter(environment=environment, segment__flag_references__isnull=False)
        .values_list(
            "feature__id",
            "feature__name",
            "segment__flag_references__prerequisite_feature__id",
            "segment__flag_references__prerequisite_feature__name",
            "segment__id",
            "segment__name",
            "segment__rules_data",
            "segment__flag_references__condition_json_path",
            "segment__is_system_segment",
        )
    ):
        assert segment_rules is not None
        edges[feature_name].append(
            {
                "feature": {"id": feature_id, "name": feature_name},
                "prerequisite": {
                    "id": prerequisite_feature_id,
                    "name": prerequisite_feature_name,
                },
                "segment": {
                    "id": segment_id,
                    "name": segment_name,
                    "rules": segment_rules,
                    "condition_json_path": condition_json_path,
                    "is_system": is_system_segment,
                },
            }
        )
    return edges


def list_flag_dependencies(
    *,
    environment: Environment,
    feature: Feature,
) -> DependencyList:
    """List the features the feature depends on in the environment."""
    return {"results": _get_dependency_edges(environment)[feature.name]}


def list_flag_dependents(
    *,
    environment: Environment,
    feature: Feature,
) -> DependencyList:
    """List the features depending on the feature in the environment."""
    return {
        "results": [
            edge
            for edges in _get_dependency_edges(environment).values()
            for edge in edges
            if edge["prerequisite"]["id"] == feature.id
        ]
    }


def create_flag_dependency(
    *,
    environment: Environment,
    feature: Feature,
    prerequisite_feature: Feature,
    author: FFAdminUser | APIKeyUser,
) -> DependencyEdge:
    """Disable the feature in the environment unless the prerequisite is enabled."""
    from features.future.services import (  # It imports this module.
        update_flag,
    )

    log = logger.bind(
        organisation__id=environment.project.organisation_id,
        project__id=environment.project_id,
        environment__key=environment.api_key,
        feature__name=feature.name,
        prerequisite_feature__name=prerequisite_feature.name,
    )
    if feature.id == prerequisite_feature.id:
        log.info("dependencies.create_failed")
        raise PrerequisiteIsSelfError()
    referencing_environment: ReferencingEnvironment = {
        "key": environment.api_key,
        "name": environment.name,
    }
    condition: SegmentCondition = {
        "property": f"$.flags[{json.dumps(prerequisite_feature.name)}].enabled",
        "operator": constants.NOT_EQUAL,
        "value": "true",
        "description": None,
    }
    segment_name = f"{feature.name}-dependencies-{environment.api_key}"
    with transaction.atomic():
        edges = _get_dependency_edges(environment)
        if existing_edges := [
            edge
            for edge in edges[feature.name]
            if edge["prerequisite"]["id"] == prerequisite_feature.id
        ]:
            log.info("dependencies.create_failed")
            raise DependencyExistsError(
                environment=referencing_environment, path=existing_edges
            )
        if prerequisite_edges := edges[prerequisite_feature.name]:
            log.info("dependencies.create_failed")
            raise PrerequisiteHasPrerequisiteError(
                environment=referencing_environment, path=prerequisite_edges
            )
        if dependent_edges := [
            edge
            for feature_edges in edges.values()
            for edge in feature_edges
            if edge["prerequisite"]["id"] == feature.id
        ]:
            log.info("dependencies.create_failed")
            raise FeatureIsPrerequisiteError(
                environment=referencing_environment, path=dependent_edges
            )
        try:
            segment = Segment.objects.get(
                project_id=environment.project_id,
                name=segment_name,
                is_system_segment=True,
            )
        except Segment.DoesNotExist:
            rules: list[SegmentRule] = [
                {"type": constants.ANY_RULE, "conditions": [condition], "rules": []}
            ]
            segment = Segment.objects.create(
                name=segment_name,
                project_id=environment.project_id,
                feature=feature,
                is_system_segment=True,
                rules_data=rules,
            )
            write_segment_rules(segment, rules)
            index_segment_flag_references(segment)
            overrides: OrderedModelQuerySet = (
                get_all_live_or_scheduled_overrides().filter(
                    environment=environment, feature=feature
                )
            )
            update_flag(
                environment=environment,
                feature=feature,
                changes={
                    "segment_overrides": [
                        {
                            "segment": {"id": segment.id},
                            "enabled": False,
                            "priority": overrides.get_next_order(),
                        }
                    ]
                },
                replace=False,
                author=author,
            )
            overrides.get(segment=segment).to(0)
        else:
            assert (rules := segment.rules_data) is not None
            rules[0]["conditions"].append(condition)
            segment.save(update_fields=["rules_data"])
            write_segment_rules(segment, rules)
            index_segment_flag_references(segment)
        _create_dependency_audit_log(
            environment=environment,
            feature=feature,
            prerequisite_feature=prerequisite_feature,
            author=author,
        )
    return map_reference_to_dependency_edge(
        feature=feature,
        reference=SegmentFlagReference.objects.select_related(
            "segment", "prerequisite_feature"
        ).get(segment=segment, prerequisite_feature=prerequisite_feature),
    )


def _create_dependency_audit_log(
    *,
    environment: Environment,
    feature: Feature,
    prerequisite_feature: Feature,
    author: FFAdminUser | APIKeyUser,
) -> None:
    user = author if isinstance(author, FFAdminUser) else None
    AuditLog.objects.create(
        environment=environment,
        project=environment.project,
        related_object_type=RelatedObjectType.FEATURE.name,
        related_object_id=feature.id,
        author=user,
        master_api_key=None if user else author.key,
        log=FEATURE_DEPENDENCY_CREATED_MESSAGE
        % (prerequisite_feature.name, feature.name),
    )

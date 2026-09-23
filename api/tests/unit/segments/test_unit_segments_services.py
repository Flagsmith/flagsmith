from datetime import timedelta
from typing import Any, cast

import pytest
from django.db import connection, reset_queries
from django.db.models import QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from flag_engine.segments.constants import EQUAL

from api_keys.models import MasterAPIKey
from audit.constants import SEGMENT_DELETED_MESSAGE
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from core.dataclasses import AuthorData
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.workflows.core.models import ChangeRequest
from organisations.models import Organisation
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from segments.services import delete_segment, get_all_live_or_scheduled_overrides
from users.models import FFAdminUser


def _create_segment_with_nested_rules(
    project: Project,
    num_rules: int = 3,
    num_nested: int = 2,
    num_conditions: int = 3,
) -> Segment:
    segment: Segment = Segment.objects.create(name="Test Segment", project=project)
    root_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

    for i in range(num_rules):
        top_rule = SegmentRule.objects.create(rule=root_rule, type=SegmentRule.ANY_RULE)
        for j in range(num_nested):
            nested_rule = SegmentRule.objects.create(
                rule=top_rule, type=SegmentRule.ALL_RULE
            )
            for k in range(num_conditions):
                Condition.objects.create(
                    rule=nested_rule,
                    property=f"prop_{i}_{j}_{k}",
                    operator=EQUAL,
                    value=f"value_{i}_{j}_{k}",
                )

    return segment


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_delete_segment__called_with_valid_segment__soft_deletes_segment(
    project: Project, admin_user: FFAdminUser
) -> None:
    # Given
    segment = Segment.objects.create(name="Test Segment", project=project)
    author = AuthorData(user=admin_user)

    # When
    delete_segment(segment, author=author)

    # Then
    segment.refresh_from_db()
    assert segment.deleted_at is not None


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_delete_segment__segment_with_nested_rules__soft_deletes_all_rules(
    project: Project, admin_user: FFAdminUser
) -> None:
    # Given
    segment = _create_segment_with_nested_rules(project)
    rule_ids = (
        list(SegmentRule.objects.filter(segment=segment).values_list("id", flat=True))
        + list(
            SegmentRule.objects.filter(rule__segment=segment).values_list(
                "id", flat=True
            )
        )
        + list(
            SegmentRule.objects.filter(rule__rule__segment=segment).values_list(
                "id", flat=True
            )
        )
    )
    author = AuthorData(user=admin_user)

    # When
    delete_segment(segment, author=author)

    # Then
    for rule_id in rule_ids:
        rule = SegmentRule.objects.get(pk=rule_id)
        assert rule.deleted_at is not None


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_delete_segment__segment_with_nested_conditions__soft_deletes_all_conditions(
    project: Project, admin_user: FFAdminUser
) -> None:
    # Given
    segment = _create_segment_with_nested_rules(project)
    condition_ids = list(
        Condition.objects.filter(rule__rule__rule__segment=segment).values_list(
            "id", flat=True
        )
    )
    author = AuthorData(user=admin_user)

    # When
    delete_segment(segment, author=author)

    # Then
    for condition_id in condition_ids:
        condition = Condition.objects.get(pk=condition_id)
        assert condition.deleted_at is not None


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_delete_segment__called_with_author__creates_audit_log(
    project: Project, admin_user: FFAdminUser
) -> None:
    # Given
    segment = Segment.objects.create(name="Test Segment", project=project)
    segment_id = segment.id
    segment_uuid = str(segment.uuid)
    author = AuthorData(user=admin_user)

    # When
    delete_segment(segment, author=author)

    # Then
    audit_log = AuditLog.objects.filter(
        related_object_id=segment_id,
        related_object_type=RelatedObjectType.SEGMENT.name,
    ).first()

    assert audit_log is not None
    assert audit_log.log == SEGMENT_DELETED_MESSAGE % "Test Segment"
    assert audit_log.author == admin_user
    assert audit_log.project == project
    assert audit_log.related_object_uuid == segment_uuid


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_delete_segment__segment_with_revision__deletes_all_versions(
    project: Project, admin_user: FFAdminUser
) -> None:
    # Given
    segment = Segment.objects.create(name="Test Segment", project=project)
    revision = segment.clone(is_revision=True)
    author = AuthorData(user=admin_user)

    # When
    delete_segment(segment, author=author)

    # Then
    segment.refresh_from_db()
    revision.refresh_from_db()
    assert segment.deleted_at is not None
    assert revision.deleted_at is not None


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_delete_segment__varying_segment_sizes__query_count_is_constant(
    project: Project, admin_user: FFAdminUser
) -> None:
    # Given
    small_segment = _create_segment_with_nested_rules(
        project, num_rules=2, num_nested=2, num_conditions=2
    )
    large_segment = _create_segment_with_nested_rules(
        project, num_rules=10, num_nested=5, num_conditions=5
    )
    author = AuthorData(user=admin_user)

    # When
    reset_queries()
    with CaptureQueriesContext(connection) as ctx_small:
        delete_segment(small_segment, author=author)
    small_query_count = len(ctx_small.captured_queries)

    reset_queries()
    with CaptureQueriesContext(connection) as ctx_large:
        delete_segment(large_segment, author=author)
    large_query_count = len(ctx_large.captured_queries)

    # Then
    # 13 for the delete, 15 for the audit log task (runs synchronously in tests)
    assert small_query_count == large_query_count == 28


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_delete_segment__segment_without_rules__soft_deletes_segment(
    project: Project, admin_user: FFAdminUser
) -> None:
    # Given
    segment = Segment.objects.create(name="Empty Segment", project=project)
    author = AuthorData(user=admin_user)

    # When
    delete_segment(segment, author=author)

    # Then
    segment.refresh_from_db()
    assert segment.deleted_at is not None


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_delete_segment__called_with_master_api_key__records_api_key_in_audit_log(
    project: Project, organisation: Organisation
) -> None:
    # Given
    segment = Segment.objects.create(name="Test Segment", project=project)
    segment_id = segment.id
    master_api_key = cast(
        MasterAPIKey,
        MasterAPIKey.objects.create_key(name="Test Key", organisation=organisation)[0],
    )
    author = AuthorData(api_key=master_api_key)

    # When
    delete_segment(segment, author=author)

    # Then
    audit_log = AuditLog.objects.filter(
        related_object_id=segment_id,
        related_object_type=RelatedObjectType.SEGMENT.name,
    ).first()

    assert audit_log is not None
    assert audit_log.master_api_key == master_api_key
    assert audit_log.author is None


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_delete_segment__segment_with_feature_segment__deletes_feature_segments(
    project: Project,
    environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given
    segment = Segment.objects.create(name="Test Segment", project=project)
    feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment
    )
    feature_segment_id = feature_segment.id
    author = AuthorData(user=admin_user)

    # When
    delete_segment(segment, author=author)

    # Then
    assert not FeatureSegment.objects.filter(id=feature_segment_id).exists()


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_delete_segment__segment_with_feature_state__cascades_to_feature_states(
    project: Project,
    environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
) -> None:
    # Given
    segment = Segment.objects.create(name="Test Segment", project=project)
    feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment
    )
    feature_state = FeatureState.objects.create(
        feature=feature,
        feature_segment=feature_segment,
        environment=environment,
    )
    feature_state_id = feature_state.id
    author = AuthorData(user=admin_user)

    # When
    delete_segment(segment, author=author)

    # Then
    assert not FeatureState.objects.filter(id=feature_state_id).exists()


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_copy_rules_and_conditions_from__source_with_nested_rules__copies_rules(
    project: Project,
) -> None:
    # Given
    source = _create_segment_with_nested_rules(
        project, num_rules=2, num_nested=2, num_conditions=3
    )
    target = Segment.objects.create(name="Target Segment", project=project)

    # When
    target.copy_rules_and_conditions_from(source)

    # Then
    source_rule_count = SegmentRule.objects.filter(segment=source).count()
    target_rule_count = SegmentRule.objects.filter(segment=target).count()
    assert target_rule_count == source_rule_count

    source_condition_count = Condition.objects.filter(
        rule__rule__rule__segment=source
    ).count()
    target_condition_count = Condition.objects.filter(
        rule__rule__rule__segment=target
    ).count()
    assert target_condition_count == source_condition_count


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_copy_rules_and_conditions_from__target_has_existing_rules__replaces_existing_rules(
    project: Project,
) -> None:
    # Given
    source = _create_segment_with_nested_rules(
        project, num_rules=3, num_nested=2, num_conditions=2
    )
    target = _create_segment_with_nested_rules(
        project, num_rules=5, num_nested=3, num_conditions=4
    )
    target.name = "Target Segment"
    target.save()

    original_target_rule_ids = list(
        SegmentRule.objects.filter(segment=target).values_list("id", flat=True)
    )

    # When
    target.copy_rules_and_conditions_from(source)

    # Then - old rules should be hard deleted
    for rule_id in original_target_rule_ids:
        assert not SegmentRule.objects.filter(id=rule_id).exists()

    # And new rules should match source
    source_rule_count = SegmentRule.objects.filter(segment=source).count()
    target_rule_count = SegmentRule.objects.filter(segment=target).count()
    assert target_rule_count == source_rule_count


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
def test_copy_rules_and_conditions_from__varying_segment_sizes__query_count_is_constant(
    project: Project,
) -> None:
    # Given
    small_source = _create_segment_with_nested_rules(
        project, num_rules=2, num_nested=2, num_conditions=2
    )
    large_source = _create_segment_with_nested_rules(
        project, num_rules=10, num_nested=5, num_conditions=5
    )
    small_target = Segment.objects.create(name="Small Target", project=project)
    large_target = Segment.objects.create(name="Large Target", project=project)

    # When
    reset_queries()
    with CaptureQueriesContext(connection) as ctx_small:
        small_target.copy_rules_and_conditions_from(small_source)
    small_query_count = len(ctx_small.captured_queries)

    reset_queries()
    with CaptureQueriesContext(connection) as ctx_large:
        large_target.copy_rules_and_conditions_from(large_source)
    large_query_count = len(ctx_large.captured_queries)

    # Then - query count should be the same (O(depth) not O(n))
    assert small_query_count == large_query_count == 10


def test_get_all_live_or_scheduled_overrides__feature_versioning_v1_uncommitted_change_request__returns_no_overrides(
    feature_segment: FeatureSegment,
    feature: Feature,
    environment: Environment,
    change_request: ChangeRequest,
) -> None:
    # Given
    FeatureState.objects.create(
        feature_segment=feature_segment,
        feature=feature,
        environment=environment,
        change_request=change_request,
        version=None,
    )

    # When
    overrides = list(get_all_live_or_scheduled_overrides())

    # Then
    assert overrides == []


@pytest.mark.usefixtures("segment_featurestate")
def test_get_all_live_or_scheduled_overrides__feature_versioning_v1_committed_change_request__returns_distinct_overrides(
    feature_segment: FeatureSegment,
    feature: Feature,
    environment: Environment,
    change_request: ChangeRequest,
    admin_user: FFAdminUser,
) -> None:
    # Given
    FeatureState.objects.create(
        feature_segment=feature_segment,
        feature=feature,
        environment=environment,
        change_request=change_request,
        version=None,
    )
    change_request.commit(admin_user)

    # When
    overrides = list(get_all_live_or_scheduled_overrides())

    # Then
    assert overrides == [feature_segment]


@pytest.mark.usefixtures("segment_featurestate")
def test_get_all_live_or_scheduled_overrides__feature_versioning_v1_scheduled_feature_change__returns_distinct_overrides(
    feature_segment: FeatureSegment,
    feature: Feature,
    environment: Environment,
    change_request: ChangeRequest,
    admin_user: FFAdminUser,
) -> None:
    # Given
    FeatureState.objects.create(
        feature_segment=feature_segment,
        feature=feature,
        environment=environment,
        change_request=change_request,
        live_from=timezone.now() + timedelta(days=1),
        version=None,
    )
    change_request.commit(admin_user)

    # When
    overrides = list(get_all_live_or_scheduled_overrides())

    # Then
    assert overrides == [feature_segment]


def test_get_all_live_or_scheduled_overrides__feature_versioning_v2_uncommitted_change_request__returns_no_overrides(
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
    change_request: ChangeRequest,
) -> None:
    # Given
    version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        change_request=change_request,
    )
    FeatureState.objects.create(
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            segment=segment,
            environment=environment_v2_versioning,
            environment_feature_version=version,
        ),
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=version,
    )

    # When
    overrides = list(get_all_live_or_scheduled_overrides())

    # Then
    assert overrides == []


def test_get_all_live_or_scheduled_overrides__feature_versioning_v2_committed_change_request__returns_distinct_overrides(
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
    change_request: ChangeRequest,
    admin_user: FFAdminUser,
) -> None:
    # Given
    live_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )
    live_version.live_from = timezone.now() - timedelta(days=1)
    live_version.save()
    FeatureState.objects.create(
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            segment=segment,
            environment=environment_v2_versioning,
            environment_feature_version=live_version,
        ),
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=live_version,
    )
    version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        change_request=change_request,
    )
    committed_override = FeatureSegment.objects.get(environment_feature_version=version)
    change_request.commit(admin_user)

    # When
    overrides = list(get_all_live_or_scheduled_overrides())

    # Then
    assert overrides == [committed_override]


def test_get_all_live_or_scheduled_overrides__feature_versioning_v2_scheduled_feature_change__returns_distinct_overrides(
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
    change_request: ChangeRequest,
    admin_user: FFAdminUser,
) -> None:
    # Given
    live_version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )
    live_override = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment_v2_versioning,
        environment_feature_version=live_version,
    )
    FeatureState.objects.create(
        feature_segment=live_override,
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=live_version,
    )
    scheduled_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        change_request=change_request,
        live_from=timezone.now() + timedelta(days=1),
    )
    scheduled_override = FeatureSegment.objects.get(
        environment_feature_version=scheduled_version
    )
    change_request.commit(admin_user)

    # When
    overrides = list(get_all_live_or_scheduled_overrides().order_by("id"))

    # Then
    assert overrides == [live_override, scheduled_override]


def _create_unrelated_versions(count: int) -> None:
    """Fill a second project with published versions."""
    organisation = Organisation.objects.create(name="Unrelated organisation")
    project = Project.objects.create(
        name="Unrelated project", organisation=organisation
    )
    environment = Environment.objects.create(
        name="Unrelated environment", project=project, use_v2_feature_versioning=True
    )
    features = Feature.objects.bulk_create(
        [Feature(project=project, name=f"unrelated_{i}") for i in range(count // 10)]
    )
    now = timezone.now()
    EnvironmentFeatureVersion.objects.bulk_create(
        [
            EnvironmentFeatureVersion(
                environment=environment,
                feature=feature,
                published_at=now,
                live_from=now - timedelta(days=version + 1),
            )
            for feature in features
            for version in range(10)
        ]
    )
    with connection.cursor() as cursor:
        cursor.execute("ANALYZE feature_versioning_environmentfeatureversion")


def _count_version_rows_read(queryset: "QuerySet[FeatureSegment]") -> int:
    """Total rows the plan reads from the versions table, per EXPLAIN ANALYZE."""
    sql, params = queryset.query.sql_with_params()
    with connection.cursor() as cursor:
        cursor.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {sql}", params)
        plan = cursor.fetchone()[0][0]["Plan"]

    def walk(node: dict[str, Any]) -> int:
        rows = 0
        if node.get("Relation Name") == "feature_versioning_environmentfeatureversion":
            rows = int(node["Actual Rows"]) * int(node["Actual Loops"])
        return rows + sum(walk(child) for child in node.get("Plans", []))

    return walk(plan)


def test_get_all_live_or_scheduled_overrides__unrelated_versions_exist__does_not_read_them(
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
) -> None:
    """Evaluating the override check must not read another project's versions.

    The check has to decide whether a feature state's version has been
    superseded. Comparing against the set of live or scheduled versions at
    large reads every version row in the installation, which is fast enough on
    a small database to pass every other test in this module and ruinous on a
    real one.
    """
    # Given
    # An override on the newest version of a feature, so the check has to look
    # at whether that version has been superseded rather than short-circuiting.
    version = EnvironmentFeatureVersion.objects.get(
        environment=environment_v2_versioning, feature=feature
    )
    override = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment_v2_versioning,
        environment_feature_version=version,
    )
    FeatureState.objects.create(
        feature_segment=override,
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=version,
    )

    # And a second project holding far more versions than the one queried.
    _create_unrelated_versions(count=2_000)

    # When
    versions_read = _count_version_rows_read(
        get_all_live_or_scheduled_overrides().filter(segment=segment)
    )

    # Then
    assert list(get_all_live_or_scheduled_overrides()) == [override]

    # The version the override points at, and nothing else.
    assert versions_read == 1

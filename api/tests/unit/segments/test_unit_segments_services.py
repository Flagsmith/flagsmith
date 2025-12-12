from typing import cast

from django.db import connection, reset_queries
from django.test.utils import CaptureQueriesContext
from flag_engine.segments.constants import EQUAL

from api_keys.models import MasterAPIKey
from audit.constants import SEGMENT_DELETED_MESSAGE
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from core.dataclasses import AuthorData
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from organisations.models import Organisation
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from segments.services import delete_segment
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


def test_delete_segment_soft_deletes_segment(
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


def test_delete_segment_soft_deletes_all_rules(
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


def test_delete_segment_soft_deletes_all_conditions(
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


def test_delete_segment_creates_audit_log(
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


def test_delete_segment_deletes_all_versions(
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


def test_delete_segment_query_count_is_constant(
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
    assert small_query_count == large_query_count == 26


def test_delete_segment_without_rules_works(
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


def test_delete_segment_with_master_api_key_records_api_key_in_audit_log(
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


def test_delete_segment_deletes_feature_segments(
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


def test_delete_segment_cascades_to_feature_states(
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

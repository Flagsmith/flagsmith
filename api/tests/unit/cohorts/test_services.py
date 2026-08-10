from flag_engine.segments.constants import IS_SET
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from cohorts.models import Cohort, CohortMembership, CohortMembershipState
from cohorts.services import (
    apply_pending_memberships,
    create_cohort,
    delete_cohort,
)
from environments.dynamodb import DynamoIdentityWrapper
from environments.models import Environment
from segments.models import Segment, SegmentRule
from users.models import FFAdminUser


def test_apply_pending_memberships__no_pending_rows__returns_false(
    cohort: Cohort,
) -> None:
    # Given
    CohortMembership.objects.create(
        cohort=cohort, identifier="user-1", state=CohortMembershipState.APPLIED
    )

    # When
    result = apply_pending_memberships(cohort)

    # Then
    assert result is False


def test_apply_pending_memberships__pending_rows__applies_and_flips(
    cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    api_key = cohort.environment.api_key
    trait_key = cohort.system_trait_key
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": f"{api_key}_member",
            "identifier": "member",
            "environment_api_key": api_key,
            "system_traits": {trait_key: True},
        }
    )
    CohortMembership.objects.create(cohort=cohort, identifier="joiner")
    CohortMembership.objects.create(
        cohort=cohort,
        identifier="member",
        state=CohortMembershipState.PENDING_REMOVE,
    )

    # When
    result = apply_pending_memberships(cohort)

    # Then
    assert result is False
    joiner_document = dynamodb_identity_wrapper.get_item(f"{api_key}_joiner")
    assert joiner_document is not None
    assert joiner_document["system_traits"] == {trait_key: True}
    member_document = dynamodb_identity_wrapper.get_item(f"{api_key}_member")
    assert member_document is not None
    assert member_document["system_traits"] == {}
    assert list(
        CohortMembership.objects.filter(cohort=cohort).values_list(
            "identifier", "state"
        )
    ) == [("joiner", CohortMembershipState.APPLIED)]


def test_apply_pending_memberships__more_rows_than_batch__returns_true(
    cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("cohorts.services.COHORT_MEMBERSHIP_APPLY_BATCH_SIZE", 1)
    CohortMembership.objects.create(cohort=cohort, identifier="user-1")
    CohortMembership.objects.create(cohort=cohort, identifier="user-2")

    # When
    result = apply_pending_memberships(cohort)

    # Then
    assert result is True
    assert (
        CohortMembership.objects.filter(
            cohort=cohort, state=CohortMembershipState.APPLIED
        ).count()
        == 1
    )


def test_apply_pending_memberships__row_transitioned_mid_write__not_flipped(
    cohort: Cohort,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    membership = CohortMembership.objects.create(cohort=cohort, identifier="user-1")
    wrapper_mock = mocker.patch("cohorts.services.DynamoIdentityWrapper").return_value

    def transition_row(**kwargs: str) -> None:
        CohortMembership.objects.filter(id=membership.id).update(
            state=CohortMembershipState.PENDING_REMOVE
        )

    wrapper_mock.set_system_trait.side_effect = transition_row

    # When
    result = apply_pending_memberships(cohort)

    # Then
    membership.refresh_from_db()
    assert membership.state == CohortMembershipState.PENDING_REMOVE
    assert result is True
    assert not log.has("membership.applied")


def test_create_cohort__valid_name__creates_segment_with_is_set_condition(
    environment: Environment,
    admin_user: FFAdminUser,
) -> None:
    # Given / When
    cohort = create_cohort(environment=environment, name="Beta users", user=admin_user)

    # Then
    segment = cohort.segment
    assert segment.name == "Beta users"
    assert segment.project == environment.project
    rule = segment.rules.get()
    assert rule.type == SegmentRule.ALL_RULE
    condition = rule.conditions.get()
    assert condition.operator == IS_SET
    assert condition.property == cohort.system_trait_key
    assert condition.created_with_segment is True


def test_create_cohort__valid_name__writes_audit_log_and_event(
    environment: Environment,
    admin_user: FFAdminUser,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    cohort = create_cohort(environment=environment, name="Beta users", user=admin_user)

    # Then
    audit_log = AuditLog.objects.get(related_object_type=RelatedObjectType.COHORT.name)
    assert audit_log.related_object_id == cohort.id
    assert audit_log.author == admin_user
    assert audit_log.log == "Cohort 'Beta users' created"
    assert log.has(
        "cohort.created",
        cohort__id=cohort.id,
        segment__id=cohort.segment_id,
        environment__id=environment.id,
    )


def test_delete_cohort__non_edge__deletes_cohort_and_segment_immediately(
    cohort: Cohort,
    admin_user: FFAdminUser,
    log: StructuredLogCapture,
) -> None:
    # Given
    CohortMembership.objects.create(
        cohort=cohort, identifier="user-1", state=CohortMembershipState.APPLIED
    )

    # When
    delete_cohort(cohort, admin_user)

    # Then
    assert not Cohort.objects.filter(id=cohort.id).exists()
    assert not Segment.objects.filter(id=cohort.segment_id).exists()
    assert not CohortMembership.objects.filter(cohort_id=cohort.id).exists()
    audit_log = AuditLog.objects.get(related_object_type=RelatedObjectType.COHORT.name)
    assert audit_log.log == f"Cohort '{cohort.segment.name}' deleted"
    assert log.has("cohort.deleted", cohort__id=cohort.id)


def test_delete_cohort__edge__drains_traits_then_deletes(
    edge_cohort: Cohort,
    admin_user: FFAdminUser,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    log: StructuredLogCapture,
) -> None:
    # Given: one member already applied (trait present), one still pending add
    api_key = edge_cohort.environment.api_key
    dynamodb_identity_wrapper.set_system_trait(
        environment_api_key=api_key,
        identifier="applied",
        trait_key=edge_cohort.system_trait_key,
    )
    CohortMembership.objects.create(
        cohort=edge_cohort, identifier="applied", state=CohortMembershipState.APPLIED
    )
    CohortMembership.objects.create(cohort=edge_cohort, identifier="pending")

    # When (synchronous task runner executes the enqueued applier inline)
    delete_cohort(edge_cohort, admin_user)

    # Then
    document = dynamodb_identity_wrapper.get_item(f"{api_key}_applied")
    assert document is not None
    assert document["system_traits"] == {}
    assert dynamodb_identity_wrapper.get_item(f"{api_key}_pending") is None
    assert not Cohort.objects.filter(id=edge_cohort.id).exists()
    assert not CohortMembership.objects.filter(cohort_id=edge_cohort.id).exists()
    assert log.has("cohort.deletion_requested", cohort__id=edge_cohort.id)

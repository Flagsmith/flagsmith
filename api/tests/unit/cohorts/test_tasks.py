import pytest
from botocore.exceptions import ClientError
from prometheus_client import REGISTRY
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from task_processor.exceptions import TaskBackoffError

from cohorts import services
from cohorts.models import Cohort, CohortMembership, CohortMembershipState
from cohorts.tasks import apply_cohort_membership_deltas
from environments.dynamodb import DynamoIdentityWrapper


def test_apply_cohort_membership_deltas__pending_adds__applies_to_documents(
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    mocker.patch("cohorts.services.identity_wrapper", dynamodb_identity_wrapper)
    api_key = edge_cohort.environment.api_key
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": f"{api_key}_seen",
            "identifier": "seen",
            "environment_api_key": api_key,
        }
    )
    CohortMembership.objects.create(cohort=edge_cohort, identifier="seen")
    CohortMembership.objects.create(cohort=edge_cohort, identifier="never-seen")

    # When
    apply_cohort_membership_deltas(cohort_id=edge_cohort.id)

    # Then
    for identifier in ("seen", "never-seen"):
        document = dynamodb_identity_wrapper.get_item(f"{api_key}_{identifier}")
        assert document is not None
        assert document["system_traits"] == {edge_cohort.system_trait_key: True}
    assert (
        CohortMembership.objects.filter(
            cohort=edge_cohort, state=CohortMembershipState.APPLIED
        ).count()
        == 2
    )
    assert log.has(
        "membership.applied", cohort__id=edge_cohort.id, adds__count=2, removes__count=0
    )


def test_apply_cohort_membership_deltas__pending_removes__drops_trait_and_rows(
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("cohorts.services.identity_wrapper", dynamodb_identity_wrapper)
    api_key = edge_cohort.environment.api_key
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": f"{api_key}_member",
            "identifier": "member",
            "environment_api_key": api_key,
            "system_traits": {edge_cohort.system_trait_key: True, "other": True},
        }
    )
    CohortMembership.objects.create(
        cohort=edge_cohort,
        identifier="member",
        state=CohortMembershipState.PENDING_REMOVE,
    )

    # When
    apply_cohort_membership_deltas(cohort_id=edge_cohort.id)

    # Then
    document = dynamodb_identity_wrapper.get_item(f"{api_key}_member")
    assert document is not None
    assert document["system_traits"] == {"other": True}
    assert not CohortMembership.objects.filter(cohort=edge_cohort).exists()


def test_apply_cohort_membership_deltas__non_edge_project__skips(
    cohort: Cohort,
    log: StructuredLogCapture,
) -> None:
    # Given
    membership = CohortMembership.objects.create(cohort=cohort, identifier="user-1")

    # When
    apply_cohort_membership_deltas(cohort_id=cohort.id)

    # Then
    membership.refresh_from_db()
    assert membership.state == CohortMembershipState.PENDING_ADD
    assert log.has(
        "membership.apply.skipped", cohort__id=cohort.id, reason="not_edge"
    )


def test_apply_cohort_membership_deltas__missing_cohort__logs_warning(
    db: None,
    log: StructuredLogCapture,
) -> None:
    # Given
    missing_cohort_id = 404404

    # When
    apply_cohort_membership_deltas(cohort_id=missing_cohort_id)

    # Then
    assert log.has(
        "membership.apply.skipped",
        cohort__id=missing_cohort_id,
        reason="cohort_missing",
        level="info",
    )


def test_apply_cohort_membership_deltas__dynamo_throttled__raises_backoff(
    edge_cohort: Cohort,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    mocker.patch("cohorts.services.identity_wrapper", mocker.MagicMock(is_enabled=True))
    mocker.patch.object(
        services,
        "apply_pending_memberships",
        side_effect=ClientError(
            {"Error": {"Code": "ProvisionedThroughputExceededException"}},
            "BatchWriteItem",
        ),
    )

    # When
    with pytest.raises(TaskBackoffError):
        apply_cohort_membership_deltas(cohort_id=edge_cohort.id)

    # Then
    assert log.has("membership.apply.throttled", cohort__id=edge_cohort.id)


def test_apply_cohort_membership_deltas__other_client_error__reraises(
    edge_cohort: Cohort,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    mocker.patch("cohorts.services.identity_wrapper", mocker.MagicMock(is_enabled=True))
    mocker.patch.object(
        services,
        "apply_pending_memberships",
        side_effect=ClientError({"Error": {"Code": "ValidationException"}}, "PutItem"),
    )

    # When
    with pytest.raises(ClientError):
        apply_cohort_membership_deltas(cohort_id=edge_cohort.id)

    # Then
    assert not log.has("membership.apply.throttled")


def test_apply_cohort_membership_deltas__more_rows_than_batch__drains_ledger(
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("cohorts.services.identity_wrapper", dynamodb_identity_wrapper)
    mocker.patch("cohorts.services.COHORT_MEMBERSHIP_APPLY_BATCH_SIZE", 1)
    CohortMembership.objects.create(cohort=edge_cohort, identifier="user-1")
    CohortMembership.objects.create(cohort=edge_cohort, identifier="user-2")

    # When (synchronous task runner executes the re-enqueued task inline)
    apply_cohort_membership_deltas(cohort_id=edge_cohort.id)

    # Then
    assert (
        CohortMembership.objects.filter(
            cohort=edge_cohort, state=CohortMembershipState.APPLIED
        ).count()
        == 2
    )


def test_apply_cohort_membership_deltas__deltas_applied__increments_metric(
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("cohorts.services.identity_wrapper", dynamodb_identity_wrapper)
    CohortMembership.objects.create(cohort=edge_cohort, identifier="user-1")
    metric = "flagsmith_cohorts_membership_deltas_applied_total"
    before = REGISTRY.get_sample_value(metric, {"operation": "add"}) or 0.0

    # When
    apply_cohort_membership_deltas(cohort_id=edge_cohort.id)

    # Then
    assert REGISTRY.get_sample_value(metric, {"operation": "add"}) == before + 1

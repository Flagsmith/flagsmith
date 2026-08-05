from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from cohorts.models import Cohort, CohortMembership, CohortMembershipState
from cohorts.services import apply_pending_memberships
from environments.dynamodb import DynamoIdentityWrapper


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


def test_apply_pending_memberships__state_changed_before_write__routes_to_new_state(
    cohort: Cohort,
    mocker: MockerFixture,
) -> None:
    # Given
    CohortMembership.objects.create(cohort=cohort, identifier="user-1")
    second = CohortMembership.objects.create(cohort=cohort, identifier="user-2")
    wrapper_mock = mocker.patch("cohorts.services.DynamoIdentityWrapper").return_value

    def transition_second_row(**kwargs: str) -> None:
        CohortMembership.objects.filter(id=second.id).update(
            state=CohortMembershipState.PENDING_REMOVE
        )
        wrapper_mock.set_system_trait.side_effect = None

    wrapper_mock.set_system_trait.side_effect = transition_second_row

    # When
    apply_pending_memberships(cohort)

    # Then
    wrapper_mock.unset_system_trait.assert_called_once_with(
        environment_api_key=cohort.environment.api_key,
        identifier="user-2",
        trait_key=cohort.system_trait_key,
    )
    assert not CohortMembership.objects.filter(id=second.id).exists()

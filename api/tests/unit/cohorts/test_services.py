import pytest
from pytest_mock import MockerFixture

from cohorts.exceptions import CohortMembershipApplyRaceError
from cohorts.models import Cohort, CohortMembership, CohortMembershipState
from cohorts.services import _apply_add, _apply_remove, apply_pending_memberships
from environments.dynamodb import DynamoIdentityWrapper


@pytest.fixture()
def patched_identity_wrapper(
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> DynamoIdentityWrapper:
    mocker.patch("cohorts.services.identity_wrapper", dynamodb_identity_wrapper)
    return dynamodb_identity_wrapper


def test_apply_add__already_member__skips_write(
    patched_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    patched_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "system_traits": {"flagsmith_cohort_x": True},
        }
    )
    update_mock = mocker.patch.object(patched_identity_wrapper.table, "update_item")
    put_mock = mocker.patch.object(patched_identity_wrapper.table, "put_item")

    # When
    _apply_add("api-key_user-1", "user-1", "api-key", "flagsmith_cohort_x")

    # Then
    update_mock.assert_not_called()
    put_mock.assert_not_called()


def test_apply_add__missing_document__creates_document(
    patched_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    composite_key = "api-key_user-1"

    # When
    _apply_add(composite_key, "user-1", "api-key", "flagsmith_cohort_x")

    # Then
    document = patched_identity_wrapper.get_item(composite_key)
    assert document is not None
    assert document["identifier"] == "user-1"
    assert document["system_traits"] == {"flagsmith_cohort_x": True}


def test_apply_remove__missing_document__no_error(
    patched_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    composite_key = "api-key_never-seen"

    # When
    _apply_remove(composite_key, "flagsmith_cohort_x")

    # Then
    assert patched_identity_wrapper.get_item(composite_key) is None


def test_apply_remove__member__removes_only_cohort_key(
    patched_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    patched_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "identity_traits": [{"trait_key": "plan", "trait_value": "pro"}],
            "system_traits": {"flagsmith_cohort_x": True, "other": True},
        }
    )

    # When
    _apply_remove("api-key_user-1", "flagsmith_cohort_x")

    # Then
    document = patched_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"other": True}
    assert document["identity_traits"] == [{"trait_key": "plan", "trait_value": "pro"}]


def test_apply_add__document_with_system_traits__sets_only_cohort_key(
    patched_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    patched_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "identity_traits": [{"trait_key": "plan", "trait_value": "pro"}],
            "system_traits": {"other": True},
        }
    )

    # When
    _apply_add("api-key_user-1", "user-1", "api-key", "flagsmith_cohort_x")

    # Then
    document = patched_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"other": True, "flagsmith_cohort_x": True}
    assert document["identity_traits"] == [{"trait_key": "plan", "trait_value": "pro"}]


def test_apply_add__document_without_system_traits__creates_map(
    patched_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    patched_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
        }
    )

    # When
    _apply_add("api-key_user-1", "user-1", "api-key", "flagsmith_cohort_x")

    # Then
    document = patched_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"flagsmith_cohort_x": True}


def test_apply_remove__trait_absent__no_error(
    patched_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    patched_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "system_traits": {"other": True},
        }
    )

    # When
    _apply_remove("api-key_user-1", "flagsmith_cohort_x")

    # Then
    document = patched_identity_wrapper.get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"other": True}


def test_apply_add__stale_missing_document_hint__retries_and_merges(
    patched_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    patched_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
            "system_traits": {"other": True},
        }
    )
    real_get_item = patched_identity_wrapper.get_item
    mocker.patch.object(
        patched_identity_wrapper,
        "get_item",
        side_effect=[None, real_get_item("api-key_user-1")],
    )

    # When
    _apply_add("api-key_user-1", "user-1", "api-key", "flagsmith_cohort_x")

    # Then
    document = real_get_item("api-key_user-1")
    assert document is not None
    assert document["system_traits"] == {"other": True, "flagsmith_cohort_x": True}


def test_apply_add__conditional_writes_keep_losing__raises(
    patched_identity_wrapper: DynamoIdentityWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    patched_identity_wrapper.put_item(
        {
            "composite_key": "api-key_user-1",
            "identifier": "user-1",
            "environment_api_key": "api-key",
        }
    )
    real_get_item = patched_identity_wrapper.get_item
    mocker.patch.object(patched_identity_wrapper, "get_item", return_value=None)

    # When
    with pytest.raises(CohortMembershipApplyRaceError):
        _apply_add("api-key_user-1", "user-1", "api-key", "flagsmith_cohort_x")

    # Then
    document = real_get_item("api-key_user-1")
    assert document is not None
    assert "system_traits" not in document


def test_apply_pending_memberships__row_transitioned_mid_flight__not_flipped(
    cohort: Cohort,
    mocker: MockerFixture,
) -> None:
    # Given
    membership = CohortMembership.objects.create(cohort=cohort, identifier="user-1")

    def transition_to_pending_remove(*args: str) -> None:
        CohortMembership.objects.filter(id=membership.id).update(
            state=CohortMembershipState.PENDING_REMOVE
        )

    mocker.patch(
        "cohorts.services._apply_add", side_effect=transition_to_pending_remove
    )

    # When
    apply_pending_memberships(cohort)

    # Then
    membership.refresh_from_db()
    assert membership.state == CohortMembershipState.PENDING_REMOVE

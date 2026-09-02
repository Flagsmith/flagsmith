import io

import pytest
from django.utils import timezone
from flag_engine.segments.constants import IS_SET
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture
from rest_framework.exceptions import ValidationError

from cohorts.models import (
    Cohort,
    CohortMembership,
    CohortMembershipState,
)
from cohorts.services import (
    _batched,
    apply_pending_memberships,
    create_cohort,
    delete_cohort,
    extract_identifiers_from_csv,
    sync_cohort_memberships_from_csv,
)
from environments.dynamodb import DynamoIdentityWrapper
from environments.identities.models import Identity
from environments.models import Environment
from segments.models import SegmentManagedBy, SegmentRule


@pytest.mark.parametrize(
    "items, size, expected",
    [
        ([], 2, []),
        ([1, 2, 3], 2, [[1, 2], [3]]),
        ([1, 2], 2, [[1, 2]]),
        ([1], 2, [[1]]),
    ],
)
def test_batched__various_lengths__yields_expected_chunks(
    items: list[int],
    size: int,
    expected: list[list[int]],
) -> None:
    # Given / When
    result = list(_batched(items, size))

    # Then
    assert result == expected


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
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    api_key = edge_cohort.environment.api_key
    trait_key = edge_cohort.system_trait_key
    dynamodb_identity_wrapper.put_item(
        {
            "composite_key": f"{api_key}_member",
            "identifier": "member",
            "environment_api_key": api_key,
            "system_traits": {trait_key: True},
        }
    )
    CohortMembership.objects.create(cohort=edge_cohort, identifier="joiner")
    CohortMembership.objects.create(
        cohort=edge_cohort,
        identifier="member",
        state=CohortMembershipState.PENDING_REMOVE,
    )

    # When
    result = apply_pending_memberships(edge_cohort)

    # Then
    assert result is False
    joiner_document = dynamodb_identity_wrapper.get_item(f"{api_key}_joiner")
    assert joiner_document is not None
    assert joiner_document["system_traits"] == {trait_key: True}
    member_document = dynamodb_identity_wrapper.get_item(f"{api_key}_member")
    assert member_document is not None
    assert member_document["system_traits"] == {}
    assert list(
        CohortMembership.objects.filter(cohort=edge_cohort).values_list(
            "identifier", "state"
        )
    ) == [("joiner", CohortMembershipState.APPLIED)]


def test_apply_pending_memberships__more_rows_than_batch__returns_true(
    cohort: Cohort,
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
    edge_cohort: Cohort,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    membership = CohortMembership.objects.create(
        cohort=edge_cohort, identifier="user-1"
    )
    wrapper_mock = mocker.patch(
        "environments.identities.system_traits.DynamoIdentityWrapper"
    ).return_value

    def transition_row(**kwargs: str) -> None:
        CohortMembership.objects.filter(id=membership.id).update(
            state=CohortMembershipState.PENDING_REMOVE
        )

    wrapper_mock.set_system_trait.side_effect = transition_row

    # When
    result = apply_pending_memberships(edge_cohort)

    # Then
    membership.refresh_from_db()
    assert membership.state == CohortMembershipState.PENDING_REMOVE
    assert result is True
    assert not log.has("membership.applied")


def test_create_cohort__valid_name__creates_segment_with_is_set_condition(
    environment: Environment,
) -> None:
    # Given / When
    cohort = create_cohort(environment=environment, name="Beta users")

    # Then
    segment = cohort.segment
    assert segment.name == "Beta users"
    assert segment.project == environment.project
    assert segment.managed_by == SegmentManagedBy.COHORT
    rule = segment.rules.get()
    assert rule.type == SegmentRule.ALL_RULE
    condition = rule.conditions.get()
    assert condition.operator == IS_SET
    assert condition.property == cohort.system_trait_key
    assert condition.created_with_segment is True


def test_create_cohort__valid_name__logs_created_event(
    environment: Environment,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    cohort = create_cohort(environment=environment, name="Beta users")

    # Then
    assert log.has(
        "cohort.created",
        cohort__id=cohort.id,
        segment__id=cohort.segment_id,
        environment__id=environment.id,
    )


def test_delete_cohort__edge__drains_traits_then_deletes(
    edge_cohort: Cohort,
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
    delete_cohort(edge_cohort)

    # Then
    document = dynamodb_identity_wrapper.get_item(f"{api_key}_applied")
    assert document is not None
    assert document["system_traits"] == {}
    assert dynamodb_identity_wrapper.get_item(f"{api_key}_pending") is None
    assert not Cohort.objects.filter(id=edge_cohort.id).exists()
    assert not CohortMembership.objects.filter(cohort_id=edge_cohort.id).exists()
    assert log.has("cohort.deletion_requested", cohort__id=edge_cohort.id)


def test_apply_pending_memberships__postgres_project__writes_system_traits(
    cohort: Cohort,
) -> None:
    # Given - a non-edge cohort, one existing identity and one never seen
    trait_key = cohort.system_trait_key
    existing = Identity.objects.create(
        environment=cohort.environment, identifier="existing"
    )
    CohortMembership.objects.create(cohort=cohort, identifier="existing")
    CohortMembership.objects.create(cohort=cohort, identifier="unseen")

    # When
    result = apply_pending_memberships(cohort)

    # Then
    assert result is False
    existing.refresh_from_db()
    assert existing.system_traits == {trait_key: True}
    unseen = Identity.objects.get(environment=cohort.environment, identifier="unseen")
    assert unseen.system_traits == {trait_key: True}
    assert sorted(
        CohortMembership.objects.filter(cohort=cohort).values_list(
            "identifier", "state"
        )
    ) == [
        ("existing", CohortMembershipState.APPLIED),
        ("unseen", CohortMembershipState.APPLIED),
    ]


def test_apply_pending_memberships__postgres_project__removes_only_own_key(
    cohort: Cohort,
) -> None:
    # Given - an identity carrying another cohort's key as well
    trait_key = cohort.system_trait_key
    identity = Identity.objects.create(
        environment=cohort.environment,
        identifier="member",
        system_traits={trait_key: True, "flagsmith_cohort_other": True},
    )
    CohortMembership.objects.create(
        cohort=cohort,
        identifier="member",
        state=CohortMembershipState.PENDING_REMOVE,
    )

    # When
    apply_pending_memberships(cohort)

    # Then
    identity.refresh_from_db()
    assert identity.system_traits == {"flagsmith_cohort_other": True}
    assert not CohortMembership.objects.filter(cohort=cohort).exists()


def test_apply_pending_memberships__removal_without_identity__deletes_membership(
    cohort: Cohort,
) -> None:
    # Given - a leaver who never had an identity row
    CohortMembership.objects.create(
        cohort=cohort,
        identifier="ghost",
        state=CohortMembershipState.PENDING_REMOVE,
    )

    # When
    apply_pending_memberships(cohort)

    # Then
    assert not CohortMembership.objects.filter(cohort=cohort).exists()
    assert not Identity.objects.filter(identifier="ghost").exists()


def test_apply_pending_memberships__system_trait_already_unset__deletes_membership(
    cohort: Cohort,
) -> None:
    # Given - a removal whose trait write already happened, as after a retry
    identity = Identity.objects.create(
        environment=cohort.environment,
        identifier="member",
        system_traits={"flagsmith_cohort_other": True},
    )
    CohortMembership.objects.create(
        cohort=cohort,
        identifier="member",
        state=CohortMembershipState.PENDING_REMOVE,
    )

    # When
    apply_pending_memberships(cohort)

    # Then
    identity.refresh_from_db()
    assert identity.system_traits == {"flagsmith_cohort_other": True}
    assert not CohortMembership.objects.filter(cohort=cohort).exists()


@pytest.mark.parametrize(
    "content, identifier_column, has_header, expected_identifiers, "
    "expected_empty, expected_duplicates, expected_too_long",
    [
        pytest.param(
            b"identity\nuser-1\nuser-2\n",
            0,
            True,
            ["user-1", "user-2"],
            0,
            0,
            0,
            id="header-single-column",
        ),
        pytest.param(
            b"user-1\nuser-2\n",
            0,
            False,
            ["user-1", "user-2"],
            0,
            0,
            0,
            id="no-header",
        ),
        pytest.param(
            b"identity,email,plan\nuser-1,a@example.com,free\nuser-2,b@example.com,pro\n",
            1,
            True,
            ["a@example.com", "b@example.com"],
            0,
            0,
            0,
            id="identifier-column-index",
        ),
        pytest.param(
            b'"Doe, Jane"\n"say ""hi"""\n',
            0,
            False,
            ["Doe, Jane", 'say "hi"'],
            0,
            0,
            0,
            id="quoted-values",
        ),
        pytest.param(
            b"identity\nuser-1\n\n  \nuser-1\nuser-2\n",
            0,
            True,
            ["user-1", "user-2"],
            1,
            1,
            0,
            id="empties-and-duplicates-counted-blank-lines-skipped",
        ),
        pytest.param(
            b"identity,plan\nuser-1\n",
            1,
            True,
            [],
            1,
            0,
            0,
            id="column-missing-from-row-counted-empty",
        ),
        pytest.param(
            b"identity\n" + b"x" * 1025 + b"\nuser-1\n",
            0,
            True,
            ["user-1"],
            0,
            0,
            1,
            id="over-long-identifier-ignored",
        ),
        pytest.param(
            ("identity\n" + "é" * 513 + "\nuser-1\n").encode(),
            0,
            True,
            ["user-1"],
            0,
            0,
            1,
            id="identifier-over-byte-limit-ignored",
        ),
        pytest.param(
            b"identity\n",
            0,
            True,
            [],
            0,
            0,
            0,
            id="header-only",
        ),
        pytest.param(
            b"\xef\xbb\xbfidentity\nuser-1\n",
            0,
            True,
            ["user-1"],
            0,
            0,
            0,
            id="utf8-bom-stripped",
        ),
    ],
)
def test_extract_identifiers_from_csv__varied_content__extracts_expected(
    content: bytes,
    identifier_column: int,
    has_header: bool,
    expected_identifiers: list[str],
    expected_empty: int,
    expected_duplicates: int,
    expected_too_long: int,
) -> None:
    # Given
    file = io.BytesIO(content)

    # When
    extraction = extract_identifiers_from_csv(
        file, identifier_column=identifier_column, has_header=has_header
    )

    # Then
    assert extraction.identifiers == expected_identifiers
    assert extraction.empty_count == expected_empty
    assert extraction.duplicate_count == expected_duplicates
    assert extraction.too_long_count == expected_too_long


def test_extract_identifiers_from_csv__unparseable_content__raises_validation_error() -> (
    None
):
    # Given
    file = io.BytesIO(b"identity\n" + b"x" * 200_000 + b"\n")

    # When / Then
    with pytest.raises(ValidationError):
        extract_identifiers_from_csv(file)


def test_sync_cohort_memberships_from_csv__first_upload__creates_and_applies_memberships(
    cohort: Cohort,
    log: StructuredLogCapture,
) -> None:
    # Given
    file = io.BytesIO(b"identity\nuser-1\nuser-2\n\nuser-2\n")

    # When (synchronous task runner executes the enqueued applier inline)
    result = sync_cohort_memberships_from_csv(cohort=cohort, file=file)

    # Then
    assert result.version == 1
    assert result.added == 2
    assert result.removed == 0
    assert result.unchanged == 0
    assert result.ignored.empty == 0
    assert result.ignored.duplicates == 1
    assert result.ignored.too_long == 0
    memberships = CohortMembership.objects.filter(cohort=cohort)
    assert {m.identifier for m in memberships} == {"user-1", "user-2"}
    assert all(m.state == CohortMembershipState.APPLIED for m in memberships)
    cohort.refresh_from_db()
    assert cohort.version == 1
    assert log.has(
        "csv.synced",
        cohort__id=cohort.id,
        environment__id=cohort.environment_id,
        cohort__version=1,
        adds__count=2,
        removes__count=0,
        unchanged__count=0,
    )


def test_sync_cohort_memberships_from_csv__reupload__computes_membership_delta(
    cohort: Cohort,
) -> None:
    # Given
    CohortMembership.objects.create(
        cohort=cohort, identifier="stay", state=CohortMembershipState.APPLIED
    )
    CohortMembership.objects.create(
        cohort=cohort, identifier="leave", state=CohortMembershipState.APPLIED
    )
    CohortMembership.objects.create(
        cohort=cohort, identifier="comeback", state=CohortMembershipState.PENDING_REMOVE
    )
    CohortMembership.objects.create(
        cohort=cohort, identifier="ghost", state=CohortMembershipState.PENDING_ADD
    )
    file = io.BytesIO(b"identity\nstay\ncomeback\nnew\n")

    # When
    result = sync_cohort_memberships_from_csv(cohort=cohort, file=file)

    # Then
    assert result.version == 1
    assert result.added == 2
    assert result.removed == 2
    assert result.unchanged == 1
    # The synchronous task runner applies the enqueued deltas inline, so
    # adds are already applied and removals are already deleted.
    states = {
        m.identifier: m.state for m in CohortMembership.objects.filter(cohort=cohort)
    }
    assert states == {
        "stay": CohortMembershipState.APPLIED,
        "comeback": CohortMembershipState.APPLIED,
        "new": CohortMembershipState.APPLIED,
    }


def test_sync_cohort_memberships_from_csv__edge_cohort__applies_traits(
    edge_cohort: Cohort,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    file = io.BytesIO(b"identity\njoiner\n")
    api_key = edge_cohort.environment.api_key

    # When
    result = sync_cohort_memberships_from_csv(cohort=edge_cohort, file=file)

    # Then
    assert result.added == 1
    document = dynamodb_identity_wrapper.get_item(f"{api_key}_joiner")
    assert document is not None
    assert document["system_traits"] == {edge_cohort.system_trait_key: True}
    membership = CohortMembership.objects.get(cohort=edge_cohort)
    assert membership.state == CohortMembershipState.APPLIED


def test_create_cohort__clickhouse_enabled__queues_membership_refresh(
    environment: Environment,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    enqueue_mock = mocker.patch(
        "segment_membership.services.enqueue_membership_refresh"
    )

    # When
    create_cohort(environment=environment, name="Beta users")

    # Then
    enqueue_mock.assert_called_once_with(environment.project)


def test_apply_pending_memberships__clickhouse_enabled__queues_delayed_refresh(
    cohort: Cohort,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.CLICKHOUSE_ENABLED = True
    settings.SEGMENT_MEMBERSHIP_DELETE_REFRESH_DELAY_SECONDS = 60
    enqueue_mock = mocker.patch(
        "segment_membership.services.enqueue_membership_refresh"
    )
    CohortMembership.objects.create(cohort=cohort, identifier="user-1")

    # When
    apply_pending_memberships(cohort)

    # Then
    enqueue_mock.assert_called_once()
    args, kwargs = enqueue_mock.call_args
    assert args == (cohort.environment.project,)
    assert kwargs["delay_until"] > timezone.now()

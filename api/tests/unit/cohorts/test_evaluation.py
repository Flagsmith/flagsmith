from cohorts.models import Cohort, CohortMembership
from cohorts.services import apply_pending_memberships, create_cohort
from environments.identities.models import Identity
from environments.models import Environment


def test_get_segments__member_of_cohort__matches_cohort_segment(
    environment: Environment,
) -> None:
    # Given
    cohort = create_cohort(environment=environment, name="Beta users")
    CohortMembership.objects.create(cohort=cohort, identifier="member")
    apply_pending_memberships(cohort)
    identity = Identity.objects.get(environment=environment, identifier="member")

    # When
    segments = identity.get_segments()

    # Then
    assert [segment.id for segment in segments] == [cohort.segment_id]


def test_get_segments__not_a_member__does_not_match_cohort_segment(
    environment: Environment,
) -> None:
    # Given
    cohort = create_cohort(environment=environment, name="Beta users")
    identity = Identity.objects.create(environment=environment, identifier="outsider")

    # When
    segments = identity.get_segments()

    # Then
    assert cohort.segment_id not in [segment.id for segment in segments]


def test_get_segments__membership_removed__stops_matching(
    environment: Environment,
) -> None:
    # Given
    cohort = create_cohort(environment=environment, name="Beta users")
    CohortMembership.objects.create(cohort=cohort, identifier="member")
    apply_pending_memberships(cohort)
    CohortMembership.objects.filter(cohort=cohort).update(state="pending_remove")
    apply_pending_memberships(cohort)
    identity = Identity.objects.get(environment=environment, identifier="member")

    # When
    segments = identity.get_segments()

    # Then
    assert cohort.segment_id not in [segment.id for segment in segments]


def test_get_segments__two_cohorts__matches_both_segments(
    environment: Environment,
) -> None:
    # Given
    first: Cohort = create_cohort(environment=environment, name="Beta users")
    second: Cohort = create_cohort(environment=environment, name="Power users")
    for cohort in (first, second):
        CohortMembership.objects.create(cohort=cohort, identifier="member")
        apply_pending_memberships(cohort)
    identity = Identity.objects.get(environment=environment, identifier="member")

    # When
    segments = identity.get_segments()

    # Then
    assert sorted(segment.id for segment in segments) == sorted(
        [first.segment_id, second.segment_id]
    )

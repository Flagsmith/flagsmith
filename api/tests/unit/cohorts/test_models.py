import pytest
from django.db.utils import IntegrityError

from cohorts.models import Cohort, CohortMembership, CohortMembershipState
from environments.models import Environment
from segments.models import Segment


def test_cohort_membership__create__defaults_to_pending_add(
    environment: Environment,
    segment: Segment,
) -> None:
    # Given
    cohort = Cohort.objects.create(environment=environment, segment=segment)

    # When
    membership = CohortMembership.objects.create(cohort=cohort, identifier="user-1")

    # Then
    assert membership.state == CohortMembershipState.PENDING_ADD


def test_cohort_membership__duplicate_identifier_in_cohort__raises_integrity_error(
    environment: Environment,
    segment: Segment,
) -> None:
    # Given
    cohort = Cohort.objects.create(environment=environment, segment=segment)
    CohortMembership.objects.create(cohort=cohort, identifier="user-1")

    # When
    with pytest.raises(IntegrityError) as exc_info:
        CohortMembership.objects.create(cohort=cohort, identifier="user-1")

    # Then
    assert "unique_cohort_membership_identifier" in str(exc_info.value)

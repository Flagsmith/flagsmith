class CohortMembershipApplyRaceError(Exception):
    """Conditional writes kept losing races for the same identity document."""

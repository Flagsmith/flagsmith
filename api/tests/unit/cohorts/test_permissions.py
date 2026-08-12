from unittest.mock import MagicMock

from cohorts.permissions import CohortPermission


def test_cohort_permission__unknown_environment__returns_false(db: None) -> None:
    # Given
    permission = CohortPermission()
    view = MagicMock(kwargs={"environment_api_key": "missing"})

    # When
    result = permission.has_permission(MagicMock(), view)

    # Then
    assert result is False

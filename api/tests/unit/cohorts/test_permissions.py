from unittest.mock import MagicMock

from cohorts.permissions import CohortPermission, CohortSyncPlanPermission


def test_cohort_permission__unknown_environment__returns_false(db: None) -> None:
    # Given
    permission = CohortPermission()
    view = MagicMock(kwargs={"environment_api_key": "missing"})

    # When
    result = permission.has_permission(MagicMock(), view)

    # Then
    assert result is False


def test_cohort_sync_plan_permission__non_sync_key_auth__returns_false() -> None:
    # Given
    permission = CohortSyncPlanPermission()
    request = MagicMock(auth=None)

    # When
    result = permission.has_permission(request, MagicMock())

    # Then
    assert result is False

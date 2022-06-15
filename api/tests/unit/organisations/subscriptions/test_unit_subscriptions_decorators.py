from unittest.mock import MagicMock

import pytest

from organisations.subscriptions.decorators import require_plan
from organisations.subscriptions.exceptions import InvalidSubscriptionPlanError


def test_require_plan_raises_exception_if_plan_invalid():
    # Given
    valid_plan_id = "plan-id"
    invalid_plan_id = "invalid-plan-id"

    mock_view = MagicMock(kwargs={"foo": "bar"})
    mock_subscription = MagicMock(plan=invalid_plan_id)

    @require_plan([valid_plan_id], mock_view, lambda v: mock_subscription)
    def test_function():
        return "foo"

    # When
    with pytest.raises(InvalidSubscriptionPlanError):
        test_function()

    # Then
    # Exception is raised


def test_require_plan_does_not_raise_exception_if_plan_valid():
    # Given
    valid_plan_id = "plan-id"

    mock_view = MagicMock()
    mock_subscription = MagicMock(plan=valid_plan_id)

    @require_plan([valid_plan_id], mock_view, lambda v: mock_subscription)
    def test_function():
        return "foo"

    # When
    res = test_function()

    # Then
    assert res == "foo"

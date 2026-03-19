from unittest.mock import MagicMock

import pytest
from rest_framework.request import Request

from organisations.subscriptions.decorators import require_plan
from organisations.subscriptions.exceptions import InvalidSubscriptionPlanError


def test_require_plan__invalid_plan__raises_exception():  # type: ignore[no-untyped-def]
    # Given
    valid_plan_id = "plan-id"
    invalid_plan_id = "invalid-plan-id"

    mock_request = MagicMock(spec=Request)
    mock_subscription = MagicMock(plan=invalid_plan_id)

    @require_plan([valid_plan_id], lambda v: mock_subscription)  # type: ignore[misc]
    def test_function(request: Request):  # type: ignore[no-untyped-def]
        return "foo"

    # When / Then
    with pytest.raises(InvalidSubscriptionPlanError):
        test_function(mock_request)


def test_require_plan__valid_plan__returns_function_result(rf):  # type: ignore[no-untyped-def]
    # Given
    valid_plan_id = "plan-id"

    mock_request = MagicMock(spec=Request)
    mock_subscription = MagicMock(plan=valid_plan_id)

    @require_plan([valid_plan_id], lambda v: mock_subscription)  # type: ignore[misc]
    def test_function(request: Request):  # type: ignore[no-untyped-def]
        return "foo"

    # When
    res = test_function(mock_request)

    # Then
    assert res == "foo"

from typing import Any, Callable

import pytest
from pytest_mock import MockerFixture

from environments.models import Environment
from features.feature_segments import permissions


@pytest.mark.parametrize(
    "get_payload, expected",
    [
        (lambda environment: {}, False),
        (lambda environment: {"environment": "invalid"}, False),
        (lambda environment: {"environment": 10_000_000}, False),  # Please don't exist
        (lambda environment: {"environment": environment.pk}, True),
    ],
)
def test_FeatureSegmentPermissions_has_permission__create_action__handles_environment_arg(
    environment: Environment,
    expected: bool,
    mocker: MockerFixture,
    get_payload: Callable[[Environment], dict[str, Any]],
) -> None:
    # Given
    view = mocker.Mock(action="create", detail=False)
    request = mocker.Mock(data=get_payload(environment))
    request.user.has_environment_permission.return_value = True

    # When
    permission = mocker.Mock(spec=permissions.FeatureSegmentPermissions)
    result = permissions.FeatureSegmentPermissions.has_permission(  # type: ignore[no-untyped-call]
        permission, request, view
    )

    # Then
    assert result is expected

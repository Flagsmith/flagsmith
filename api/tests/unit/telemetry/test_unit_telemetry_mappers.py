import typing

import pytest

from telemetry.mappers import map_view_kwargs_to_resolved_ids
from telemetry.types import ResolvedIds


@pytest.mark.parametrize(
    "view_kwargs, expected_ids",
    [
        ({}, {}),
        ({"pk": "7"}, {}),
        # Routers capture strings, path converters ints
        ({"project_pk": "42"}, {"project__id": 42}),
        ({"project_pk": 42, "feature_pk": 3}, {"project__id": 42, "feature__id": 3}),
        (
            {"environment_api_key": "key", "feature_pk": "3"},
            {"environment__api_key": "key", "feature__id": 3},
        ),
        ({"project_pk": "not-an-id", "feature_pk": "3"}, {"feature__id": 3}),
        # Digits that `int` can't parse, e.g. captured by routers
        ({"project_pk": "²", "feature_pk": "²"}, {}),
        ({"project_pk": None, "feature_pk": ""}, {}),
    ],
)
def test_map_view_kwargs_to_resolved_ids__view_kwargs__returns_expected_ids(
    view_kwargs: dict[str, typing.Any],
    expected_ids: ResolvedIds,
) -> None:
    # Given / When
    # NOTE: Without database access, any query would fail the test
    ids = map_view_kwargs_to_resolved_ids(view_kwargs)

    # Then
    assert ids == expected_ids

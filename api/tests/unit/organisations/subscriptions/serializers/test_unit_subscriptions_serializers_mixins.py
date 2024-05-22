from unittest.mock import MagicMock

import pytest
from rest_framework import serializers

from organisations.models import Subscription
from organisations.subscriptions.serializers.mixins import (
    ReadOnlyIfNotValidPlanMixin,
)


@pytest.mark.parametrize(
    "plan_id, invalid_plans_, invalid_plans_regex_",
    (
        ("invalid-plan-id", ("invalid-plan-id",), ""),
        ("invalid-plan-id", tuple(), "invalid-.*"),
    ),
)
def test_read_only_if_not_valid_plan_mixin_sets_read_only_if_plan_not_valid(
    plan_id: str, invalid_plans_: list[str], invalid_plans_regex_: str
) -> None:
    # Given
    mock_view = MagicMock()

    class MySerializer(ReadOnlyIfNotValidPlanMixin, serializers.Serializer):
        field_names = ("foo",)

        invalid_plans = invalid_plans_
        invalid_plans_regex = invalid_plans_regex_

        foo = serializers.CharField()

        def get_subscription(self) -> Subscription:
            return MagicMock(plan=plan_id)

    serializer = MySerializer(data={"foo": "bar"}, context={"view": mock_view})

    # When
    serializer.is_valid()

    # Then
    assert "foo" not in serializer.validated_data
    assert serializer.fields["foo"].read_only is True


def test_read_only_if_not_valid_plan_mixin_does_not_set_read_only_if_plan_valid():
    # Given
    valid_plan_id = "plan-id"
    invalid_plan_id = "invalid-plan-id"
    invalid_plans_regex_ = r"^another-invalid-plan-id-.*$"

    mock_view = MagicMock()

    class MySerializer(ReadOnlyIfNotValidPlanMixin, serializers.Serializer):
        invalid_plans = (invalid_plan_id,)
        field_names = ("foo",)
        invalid_plans_regex = invalid_plans_regex_

        foo = serializers.CharField()

        def get_subscription(self) -> Subscription:
            return MagicMock(plan=valid_plan_id)

    serializer = MySerializer(data={"foo": "bar"}, context={"view": mock_view})

    # When
    serializer.is_valid()

    # Then
    assert "foo" in serializer.validated_data
    assert serializer.fields["foo"].read_only is False

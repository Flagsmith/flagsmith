from types import SimpleNamespace

from pytest_mock import MockerFixture

from api.openapi import MINIMUM_PLAN_EXTENSION, AutoSchema
from organisations.subscriptions.constants import SubscriptionPlanFamily
from organisations.subscriptions.permissions import require_minimum_plan


def test_auto_schema_get_operation__plan_gated_view__adds_minimum_plan_extension(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "drf_spectacular.openapi.AutoSchema.get_operation",
        return_value={"operationId": "op"},
    )
    schema = AutoSchema()
    schema.view = SimpleNamespace(
        permission_classes=[require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)]
    )

    # When
    operation = schema.get_operation()

    # Then
    assert operation is not None
    assert operation[MINIMUM_PLAN_EXTENSION] == SubscriptionPlanFamily.SCALE_UP.value


def test_auto_schema_get_operation__unrestricted_view__omits_extension(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "drf_spectacular.openapi.AutoSchema.get_operation",
        return_value={"operationId": "op"},
    )
    schema = AutoSchema()
    schema.view = SimpleNamespace(permission_classes=[])

    # When
    operation = schema.get_operation()

    # Then
    assert operation is not None
    assert MINIMUM_PLAN_EXTENSION not in operation


def test_auto_schema_get_operation__no_operation__returns_none(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "drf_spectacular.openapi.AutoSchema.get_operation",
        return_value=None,
    )
    schema = AutoSchema()

    # When / Then
    assert schema.get_operation() is None

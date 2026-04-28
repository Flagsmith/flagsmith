from unittest.mock import MagicMock

import pytest
from pytest_lazy_fixtures import lf as lazy_fixture
from rest_framework.request import Request

from organisations.models import Organisation, Subscription
from organisations.subscriptions.constants import SubscriptionPlanFamily
from organisations.subscriptions.permissions import require_minimum_plan


@pytest.mark.saas_mode
@pytest.mark.parametrize(
    "subscription_fixture, expected",
    [
        (lazy_fixture("free_subscription"), False),
        (lazy_fixture("startup_subscription"), False),
        (lazy_fixture("scale_up_subscription"), True),
        (lazy_fixture("enterprise_subscription"), True),
    ],
)
def test_require_minimum_plan__has_permission__plan_matrix(
    organisation: Organisation,
    subscription_fixture: Subscription,
    expected: bool,
) -> None:
    # Given
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    request = MagicMock(spec=Request)
    request.data = {"organisation": organisation.id}
    request.query_params = {}

    # When / Then
    assert permission.has_permission(request, MagicMock()) is expected


@pytest.mark.saas_mode
@pytest.mark.parametrize(
    "subscription_fixture, expected",
    [
        (lazy_fixture("free_subscription"), False),
        (lazy_fixture("startup_subscription"), False),
        (lazy_fixture("scale_up_subscription"), True),
        (lazy_fixture("enterprise_subscription"), True),
    ],
)
def test_require_minimum_plan__has_object_permission__plan_matrix(
    organisation: Organisation,
    subscription_fixture: Subscription,
    expected: bool,
) -> None:
    # Given
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    obj = MagicMock()
    obj.organisation = organisation

    # When / Then
    assert (
        permission.has_object_permission(MagicMock(spec=Request), MagicMock(), obj)
        is expected
    )


@pytest.mark.saas_mode
@pytest.mark.parametrize("source", ["data", "query_params"])
def test_require_minimum_plan__organisation_lookup__reads_from_data_and_query_params(
    organisation: Organisation,
    free_subscription: Subscription,
    source: str,
) -> None:
    # Given
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    request = MagicMock(spec=Request)
    request.data = {}
    request.query_params = {}
    setattr(request, source, {"organisation": organisation.id})

    # When / Then
    assert permission.has_permission(request, MagicMock()) is False


@pytest.mark.saas_mode
def test_require_minimum_plan__no_organisation_in_request__defers_to_object_level() -> (
    None
):
    # Given
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    request = MagicMock(spec=Request)
    request.data = {}
    request.query_params = {}

    # When / Then
    assert permission.has_permission(request, MagicMock()) is True


@pytest.mark.saas_mode
def test_require_minimum_plan__unknown_organisation_id__returns_false(
    db: None,
) -> None:
    # Given
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    request = MagicMock(spec=Request)
    request.data = {"organisation": 999999}
    request.query_params = {}

    # When / Then
    assert permission.has_permission(request, MagicMock()) is False


@pytest.mark.saas_mode
def test_require_minimum_plan_has_object_permission__obj_without_organisation__returns_false() -> (
    None
):
    # Given
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()

    # When / Then
    assert (
        permission.has_object_permission(MagicMock(spec=Request), MagicMock(), object())
        is False
    )


@pytest.mark.saas_mode
@pytest.mark.parametrize(
    "minimum, subscription_fixture, allowed",
    [
        (SubscriptionPlanFamily.START_UP, lazy_fixture("free_subscription"), False),
        (SubscriptionPlanFamily.START_UP, lazy_fixture("startup_subscription"), True),
        (SubscriptionPlanFamily.SCALE_UP, lazy_fixture("startup_subscription"), False),
        (SubscriptionPlanFamily.SCALE_UP, lazy_fixture("scale_up_subscription"), True),
        (
            SubscriptionPlanFamily.ENTERPRISE,
            lazy_fixture("scale_up_subscription"),
            False,
        ),
        (
            SubscriptionPlanFamily.ENTERPRISE,
            lazy_fixture("enterprise_subscription"),
            True,
        ),
    ],
)
def test_require_minimum_plan__plan_hierarchy__honours_ordering(
    organisation: Organisation,
    minimum: SubscriptionPlanFamily,
    subscription_fixture: Subscription,
    allowed: bool,
) -> None:
    # Given
    permission = require_minimum_plan(minimum)()
    request = MagicMock(spec=Request)
    request.data = {"organisation": organisation.id}
    request.query_params = {}

    # When / Then
    assert permission.has_permission(request, MagicMock()) is allowed


def test_require_minimum_plan__self_hosted__bypasses_check(
    organisation: Organisation,
    free_subscription: Subscription,
) -> None:
    # Given
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    request = MagicMock(spec=Request)
    request.data = {"organisation": organisation.id}
    request.query_params = {}
    obj = MagicMock()
    obj.organisation = organisation

    # When / Then
    assert permission.has_permission(request, MagicMock()) is True
    assert (
        permission.has_object_permission(MagicMock(spec=Request), MagicMock(), obj)
        is True
    )

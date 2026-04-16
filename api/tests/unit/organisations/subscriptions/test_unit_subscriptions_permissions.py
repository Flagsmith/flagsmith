from unittest.mock import MagicMock

import pytest
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from pytest_mock import MockerFixture
from rest_framework.request import Request

from organisations.models import Organisation, Subscription
from organisations.subscriptions.constants import SubscriptionPlanFamily
from organisations.subscriptions.permissions import require_minimum_plan


@pytest.fixture
def saas(mocker: MockerFixture) -> None:
    mocker.patch(
        "organisations.subscriptions.permissions.is_saas", return_value=True
    )


@pytest.fixture
def self_hosted(mocker: MockerFixture) -> None:
    mocker.patch(
        "organisations.subscriptions.permissions.is_saas", return_value=False
    )


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
    saas: None,
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
    saas: None,
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


@pytest.mark.parametrize("source", ["data", "query_params"])
def test_require_minimum_plan__organisation_lookup__reads_from_data_and_query_params(
    saas: None,
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


def test_require_minimum_plan__no_organisation_in_request__defers_to_object_level(
    saas: None,
) -> None:
    # Given
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    request = MagicMock(spec=Request)
    request.data = {}
    request.query_params = {}

    # When / Then
    assert permission.has_permission(request, MagicMock()) is True


def test_require_minimum_plan__unknown_organisation_id__returns_false(
    saas: None,
    db: None,
) -> None:
    # Given
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    request = MagicMock(spec=Request)
    request.data = {"organisation": 999999}
    request.query_params = {}

    # When / Then
    assert permission.has_permission(request, MagicMock()) is False


def test_require_minimum_plan__has_object_permission__no_organisation_attr__returns_false(
    saas: None,
) -> None:
    # Given
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()

    # When / Then
    assert (
        permission.has_object_permission(
            MagicMock(spec=Request), MagicMock(), object()
        )
        is False
    )


@pytest.mark.parametrize(
    "minimum, subscription_fixture, allowed",
    [
        (SubscriptionPlanFamily.START_UP, lazy_fixture("free_subscription"), False),
        (SubscriptionPlanFamily.START_UP, lazy_fixture("startup_subscription"), True),
        (SubscriptionPlanFamily.START_UP, lazy_fixture("scale_up_subscription"), True),
        (
            SubscriptionPlanFamily.START_UP,
            lazy_fixture("enterprise_subscription"),
            True,
        ),
        (SubscriptionPlanFamily.SCALE_UP, lazy_fixture("startup_subscription"), False),
        (SubscriptionPlanFamily.SCALE_UP, lazy_fixture("scale_up_subscription"), True),
        (
            SubscriptionPlanFamily.SCALE_UP,
            lazy_fixture("enterprise_subscription"),
            True,
        ),
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
    saas: None,
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


@pytest.mark.parametrize(
    "plan_id",
    [
        "scale-up-v2",
        "scale-up-monthly",
        "enterprise-saas-monthly-v2",  # used for trials
    ],
)
def test_require_minimum_plan__real_world_plan_ids__allowed(
    saas: None,
    organisation: Organisation,
    plan_id: str,
) -> None:
    # Given
    Subscription.objects.filter(organisation=organisation).update(
        plan=plan_id, subscription_id="subscription-id"
    )
    organisation.refresh_from_db()

    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    request = MagicMock(spec=Request)
    request.data = {"organisation": organisation.id}
    request.query_params = {}

    # When / Then
    assert permission.has_permission(request, MagicMock()) is True


def test_require_minimum_plan__self_hosted__has_permission__bypasses_check(
    self_hosted: None,
    organisation: Organisation,
    free_subscription: Subscription,
) -> None:
    # Given a self-hosted deployment, even a free-plan organisation is permitted.
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    request = MagicMock(spec=Request)
    request.data = {"organisation": organisation.id}
    request.query_params = {}

    # When / Then
    assert permission.has_permission(request, MagicMock()) is True


def test_require_minimum_plan__self_hosted__has_object_permission__bypasses_check(
    self_hosted: None,
    organisation: Organisation,
    free_subscription: Subscription,
) -> None:
    # Given a self-hosted deployment, object-level checks are also bypassed.
    permission = require_minimum_plan(SubscriptionPlanFamily.SCALE_UP)()
    obj = MagicMock()
    obj.organisation = organisation

    # When / Then
    assert (
        permission.has_object_permission(MagicMock(spec=Request), MagicMock(), obj)
        is True
    )

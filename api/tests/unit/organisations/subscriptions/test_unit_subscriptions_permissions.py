from unittest.mock import MagicMock

import pytest
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from rest_framework.request import Request

from environments.models import Environment
from organisations.models import Organisation, Subscription
from organisations.subscriptions.constants import SubscriptionPlanFamily
from organisations.subscriptions.permissions import (
    organisation_from_environment_api_key,
    organisation_from_organisation_pk,
    organisation_from_project_pk,
    require_minimum_plan,
)
from projects.models import Project


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


@pytest.mark.parametrize(
    "resolver, kwarg_key",
    [
        (organisation_from_organisation_pk, "organisation_pk"),
        (organisation_from_project_pk, "project_pk"),
        (organisation_from_environment_api_key, "environment_api_key"),
    ],
)
def test_organisation_resolver__missing_kwarg__returns_none(
    db: None,
    resolver: object,
    kwarg_key: str,
) -> None:
    # Given
    view = MagicMock()
    view.kwargs = {}

    # When / Then
    assert resolver(MagicMock(spec=Request), view) is None  # type: ignore[operator]


def test_organisation_resolver__valid_kwarg__returns_organisation(
    organisation: Organisation,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    cases = [
        (organisation_from_organisation_pk, {"organisation_pk": organisation.pk}),
        (organisation_from_project_pk, {"project_pk": project.pk}),
        (
            organisation_from_environment_api_key,
            {"environment_api_key": environment.api_key},
        ),
    ]

    for resolver, kwargs in cases:
        view = MagicMock()
        view.kwargs = kwargs

        # When / Then
        assert resolver(MagicMock(spec=Request), view) == organisation


@pytest.mark.saas_mode
@pytest.mark.parametrize(
    "method, subscription_fixture, expected",
    [
        ("has_permission", lazy_fixture("free_subscription"), False),
        ("has_permission", lazy_fixture("scale_up_subscription"), True),
        ("has_object_permission", lazy_fixture("free_subscription"), False),
        ("has_object_permission", lazy_fixture("scale_up_subscription"), True),
    ],
)
def test_require_minimum_plan__get_organisation_callback__checks_plan(
    organisation: Organisation,
    subscription_fixture: Subscription,
    method: str,
    expected: bool,
) -> None:
    # Given
    permission = require_minimum_plan(
        SubscriptionPlanFamily.SCALE_UP,
        get_organisation=lambda req, view: organisation,
    )()
    request = MagicMock(spec=Request)
    request.data = {}
    request.query_params = {}

    # When / Then
    assert (
        getattr(permission, method)(
            request, MagicMock(), *(() if method == "has_permission" else (object(),))
        )
        is expected
    )


@pytest.mark.saas_mode
def test_require_minimum_plan_has_permission__get_organisation_returns_none__returns_false(
    db: None,
) -> None:
    # Given
    permission = require_minimum_plan(
        SubscriptionPlanFamily.SCALE_UP,
        get_organisation=lambda req, view: None,
    )()
    request = MagicMock(spec=Request)
    request.data = {}
    request.query_params = {}

    # When / Then
    assert permission.has_permission(request, MagicMock()) is False


@pytest.mark.saas_mode
@pytest.mark.parametrize(
    "subscription_fixture, expected",
    [
        (lazy_fixture("free_subscription"), False),
        (lazy_fixture("scale_up_subscription"), True),
    ],
)
def test_require_minimum_plan_has_object_permission__get_organisation_from_object__checks_plan(
    organisation: Organisation,
    subscription_fixture: Subscription,
    expected: bool,
) -> None:
    # Given
    permission = require_minimum_plan(
        SubscriptionPlanFamily.SCALE_UP,
        get_organisation_from_object=lambda o: organisation,
    )()

    # When / Then
    assert (
        permission.has_object_permission(MagicMock(spec=Request), MagicMock(), object())
        is expected
    )


@pytest.mark.saas_mode
def test_require_minimum_plan_has_permission__no_organisation_resolver__defers_to_object_level(
    db: None,
) -> None:
    # Given
    permission = require_minimum_plan(
        SubscriptionPlanFamily.SCALE_UP,
        get_organisation_from_object=lambda o: None,
    )()
    request = MagicMock(spec=Request)
    request.data = {}
    request.query_params = {}

    # When / Then
    assert permission.has_permission(request, MagicMock()) is True


def test_require_minimum_plan__self_hosted_with_callbacks__bypasses_check(
    organisation: Organisation,
    free_subscription: Subscription,
) -> None:
    # Given
    permission = require_minimum_plan(
        SubscriptionPlanFamily.SCALE_UP,
        get_organisation=lambda req, view: organisation,
    )()
    request = MagicMock(spec=Request)

    # When / Then
    assert permission.has_permission(request, MagicMock()) is True
    assert permission.has_object_permission(request, MagicMock(), object()) is True

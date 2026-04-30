from collections.abc import Callable

from common.core.utils import is_saas
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from organisations.models import Organisation
from organisations.subscriptions.constants import SubscriptionPlanFamily

_PLAN_RANK = {
    SubscriptionPlanFamily.FREE: 0,
    SubscriptionPlanFamily.START_UP: 1,
    SubscriptionPlanFamily.SCALE_UP: 2,
    SubscriptionPlanFamily.ENTERPRISE: 3,
}


def organisation_from_organisation_pk(
    request: Request, view: APIView
) -> Organisation | None:
    org_pk = view.kwargs.get("organisation_pk")
    if not org_pk:
        return None
    result: Organisation | None = (
        Organisation.objects.select_related("subscription").filter(pk=org_pk).first()
    )
    return result


def organisation_from_project_pk(
    request: Request, view: APIView
) -> Organisation | None:
    project_pk = view.kwargs.get("project_pk")
    if not project_pk:
        return None
    result: Organisation | None = (
        Organisation.objects.select_related("subscription")
        .filter(projects__pk=project_pk)
        .first()
    )
    return result


def organisation_from_environment_api_key(
    request: Request,
    view: APIView,
) -> Organisation | None:
    api_key = view.kwargs.get("environment_api_key")
    if not api_key:
        return None
    result: Organisation | None = (
        Organisation.objects.select_related("subscription")
        .filter(projects__environments__api_key=api_key)
        .first()
    )
    return result


def require_minimum_plan(
    minimum: SubscriptionPlanFamily,
    *,
    get_organisation: Callable[[Request, APIView], Organisation | None] | None = None,
    get_organisation_from_object: (
        Callable[[object], Organisation | None] | None
    ) = None,
) -> type[BasePermission]:
    """
    Return a DRF permission class that requires the organisation associated
    with the request to be on `minimum` plan family or higher.

    On non-SaaS deployments (self-hosted OSS / Enterprise), plan gating is
    always bypassed. These deployments don't use Chargebee subscriptions —
    entitlements are handled via the enterprise licence file instead, so
    `Subscription.plan` is typically `"free"` and not meaningful.

    On SaaS, the organisation is resolved via (in order of priority):
      - The `get_organisation(request, view)` callback, if provided.
      - `request.data["organisation"]` or `?organisation=` for list/create.
      - The `get_organisation_from_object(obj)` callback (object-level only).
      - `obj.organisation` for detail actions (via `has_object_permission`).
    """
    min_rank = _PLAN_RANK[minimum]

    def _meets(org: Organisation) -> bool:
        return _PLAN_RANK.get(org.subscription.subscription_plan_family, -1) >= min_rank

    class _MinimumPlanPermission(BasePermission):
        message = f"This resource requires a {minimum.value} plan or above."

        def has_permission(self, request: Request, view: APIView) -> bool:
            if not is_saas():
                return True

            if get_organisation is not None:
                org = get_organisation(request, view)
                return org is not None and _meets(org)

            org_id = request.data.get("organisation") or request.query_params.get(
                "organisation"
            )
            if not org_id:
                return True
            org = Organisation.objects.filter(id=org_id).first()
            return org is not None and _meets(org)

        def has_object_permission(
            self, request: Request, view: APIView, obj: object
        ) -> bool:
            if not is_saas():
                return True

            if get_organisation is not None:
                org = get_organisation(request, view)
            elif get_organisation_from_object is not None:
                org = get_organisation_from_object(obj)
            else:
                org = getattr(obj, "organisation", None)

            return isinstance(org, Organisation) and _meets(org)

    return _MinimumPlanPermission

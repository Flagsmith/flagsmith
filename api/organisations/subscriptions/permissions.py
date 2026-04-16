from __future__ import annotations

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


def require_minimum_plan(minimum: SubscriptionPlanFamily) -> type[BasePermission]:
    """
    Return a DRF permission class that requires the organisation associated
    with the request to be on `minimum` plan family or higher.

    On non-SaaS deployments (self-hosted OSS / Enterprise), plan gating is
    always bypassed. These deployments don't use Chargebee subscriptions —
    entitlements are handled via the enterprise licence file instead, so
    `Subscription.plan` is typically `"free"` and not meaningful.

    On SaaS, the organisation is read from:
      - `obj.organisation` for detail actions (via `has_object_permission`)
      - `request.data["organisation"]` or `?organisation=` for list/create
    """
    min_rank = _PLAN_RANK[minimum]

    def _meets(org: Organisation) -> bool:
        sub = getattr(org, "subscription", None)
        if sub is None:
            return False
        return _PLAN_RANK.get(sub.subscription_plan_family, -1) >= min_rank

    class _MinimumPlanPermission(BasePermission):
        message = f"This resource requires a {minimum.value} plan or above."

        def has_permission(self, request: Request, view: APIView) -> bool:
            if not is_saas():
                return True
            org_id = request.data.get("organisation") or request.query_params.get(
                "organisation"
            )
            if not org_id:
                # defer to has_object_permission for detail actions;
                # list/create without an org will be caught by the view's validation
                return True
            org = Organisation.objects.filter(id=org_id).first()
            return org is not None and _meets(org)

        def has_object_permission(
            self, request: Request, view: APIView, obj: object
        ) -> bool:
            if not is_saas():
                return True
            org = getattr(obj, "organisation", None)
            return isinstance(org, Organisation) and _meets(org)

    return _MinimumPlanPermission

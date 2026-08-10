from common.environments.permissions import VIEW_ENVIRONMENT
from common.projects.permissions import MANAGE_SEGMENTS
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from environments.models import Environment
from organisations.subscriptions.constants import SubscriptionPlanFamily
from organisations.subscriptions.permissions import require_minimum_plan
from users.models import FFAdminUser

_READ_ACTIONS = ("list", "retrieve")

_MinimumPlanPermission = require_minimum_plan(SubscriptionPlanFamily.START_UP)


class CohortPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        try:
            environment = Environment.objects.get(
                api_key=view.kwargs.get("environment_api_key")
            )
        except Environment.DoesNotExist:
            return False
        # Cohorts are a paid feature. The plan permission reads the
        # organisation off the object it's given; the project carries it.
        plan_permission = _MinimumPlanPermission()
        if not plan_permission.has_object_permission(
            request, view, environment.project
        ):
            # `message` exists on the concrete class the factory returns, but
            # its return annotation (`type[BasePermission]`) hides it.
            raise PermissionDenied(plan_permission.message)  # type: ignore[attr-defined]
        user: FFAdminUser = request.user  # type: ignore[assignment]
        if getattr(view, "action", None) in _READ_ACTIONS:
            return user.has_environment_permission(VIEW_ENVIRONMENT, environment)
        return user.has_project_permission(MANAGE_SEGMENTS, environment.project)

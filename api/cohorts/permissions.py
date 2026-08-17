from common.environments.permissions import (
    MANAGE_SEGMENT_OVERRIDES,
    VIEW_ENVIRONMENT,
)
from common.projects.permissions import MANAGE_SEGMENTS
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from cohorts.models import CohortSyncKey
from environments.models import Environment
from organisations.subscriptions.constants import SubscriptionPlanFamily
from organisations.subscriptions.permissions import require_minimum_plan
from users.models import FFAdminUser

_READ_ACTIONS = ("list", "retrieve")


class HasCohortSyncKey(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return isinstance(request.auth, CohortSyncKey)


_MinimumStartupPlan = require_minimum_plan(SubscriptionPlanFamily.START_UP)


class CohortPlanPermission(_MinimumStartupPlan):  # type: ignore[misc,valid-type]
    def has_permission(self, request: Request, view: APIView) -> bool:
        try:
            environment = Environment.objects.get(
                api_key=view.kwargs.get("environment_api_key")
            )
        except Environment.DoesNotExist:
            return False
        # The base class reads the organisation from an `organisation` request
        # param our URLs don't carry; the project provides it instead.
        return bool(super().has_object_permission(request, view, environment.project))

    def has_object_permission(
        self, request: Request, view: APIView, obj: object
    ) -> bool:
        # DRF hands us a Cohort here, which doesn't carry an organisation;
        # re-run the environment-based check instead.
        return self.has_permission(request, view)


class CohortPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        try:
            environment = Environment.objects.get(
                api_key=view.kwargs.get("environment_api_key")
            )
        except Environment.DoesNotExist:
            return False
        user: FFAdminUser = request.user  # type: ignore[assignment]
        if not user.has_environment_permission(VIEW_ENVIRONMENT, environment):
            return False
        if getattr(view, "action", None) in _READ_ACTIONS:
            return True
        return user.has_environment_permission(
            MANAGE_SEGMENT_OVERRIDES, environment
        ) and user.has_project_permission(MANAGE_SEGMENTS, environment.project)

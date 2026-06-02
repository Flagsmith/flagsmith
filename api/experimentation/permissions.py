from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from environments.models import Environment
from experimentation.services import (
    is_experiment_feature_enabled,
    is_warehouse_feature_enabled,
)
from users.models import FFAdminUser


class WarehouseConnectionPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        try:
            environment = Environment.objects.get(
                api_key=view.kwargs.get("environment_api_key")
            )
        except Environment.DoesNotExist:
            return False

        if not is_warehouse_feature_enabled(environment.project.organisation):
            return False

        user: FFAdminUser = request.user  # type: ignore[assignment]
        return user.is_environment_admin(environment)


class ExperimentPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        try:
            environment = Environment.objects.get(
                api_key=view.kwargs.get("environment_api_key")
            )
        except Environment.DoesNotExist:
            return False

        if not is_experiment_feature_enabled(environment.project.organisation):
            return False

        user: FFAdminUser = request.user  # type: ignore[assignment]
        return user.is_environment_admin(environment)


class MetricPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        try:
            environment = Environment.objects.get(
                api_key=view.kwargs.get("environment_api_key")
            )
        except Environment.DoesNotExist:
            return False

        if not is_experiment_feature_enabled(environment.project.organisation):
            return False

        user: FFAdminUser = request.user  # type: ignore[assignment]
        return user.is_environment_admin(environment)

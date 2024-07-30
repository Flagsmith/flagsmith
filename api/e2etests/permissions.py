from django.views import View
from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class E2ETestPermission(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return getattr(request, "is_e2e", False) is True


class E2ETestPermissionMixin:
    def has_permission(self, request: Request, view: View) -> bool:
        if getattr(request, "is_e2e", False) is True:
            return True
        return super().has_permission(request, view)

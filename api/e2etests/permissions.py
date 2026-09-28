from django.views import View
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from e2etests.helpers import is_e2e_request


class E2ETestPermission(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        return is_e2e_request(request)

from django.http import HttpRequest
from rest_framework.permissions import BasePermission


class HasMasterAPIKEY(BasePermission):
    def has_permission(self, request: HttpRequest, view: str) -> bool:
        master_api_key = getattr(request, "master_api_key", None)
        return bool(master_api_key)

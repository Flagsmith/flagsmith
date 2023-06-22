import os

from rest_framework.permissions import BasePermission


class E2ETestPermission(BasePermission):
    def has_permission(self, request, view):
        os.environ.setdefault("E2E_TEST_AUTH_TOKEN", "some-token")

        if "E2E_TEST_AUTH_TOKEN" not in os.environ:
            return False
        return (
            request.META.get("HTTP_X_E2E_TEST_AUTH_TOKEN")
            == os.environ["E2E_TEST_AUTH_TOKEN"]
        )

from rest_framework.permissions import BasePermission

from environments.models import Environment


class FeatureStatePermissions(BasePermission):
    def has_permission(self, request, view):
        try:
            if view.action == "create":
                if request.data.get("environment"):
                    environment = Environment.objects.get(request.data["environment"])
                    return request.user.is_environment_admin(environment)

            # detail view so we can check defer to object permissions
            return view.detail

        except Environment.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        # we only care about create permissions
        return False

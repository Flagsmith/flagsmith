from django.db.models import Q
from rest_framework import exceptions
from rest_framework.permissions import BasePermission

from environments.models import Environment
from projects.models import Project


class EnvironmentKeyPermissions(BasePermission):
    def has_permission(self, request, view):
        # Authentication class will set the environment on the request if it exists
        if hasattr(request, "environment"):
            return True

        raise exceptions.PermissionDenied("Missing or invalid Environment Key")

    def has_object_permission(self, request, view, obj):
        """
        This method is only called if has_permission returns true so we can safely return true for all requests here.
        """
        return True


class EnvironmentPermissions(BasePermission):
    def has_permission(self, request, view):
        if view.action not in ["clone", "create"]:
            # return true as all users can list and specific object permissions will be handled later
            return True
        try:

            if view.action == "clone":
                api_key = request.path_info.split("/")[-3]
                project_lookup = Q(environments__api_key=api_key)

            elif view.action == "create":
                project_id = request.data.get("project")
                project_lookup = Q(id=project_id)

            project = Project.objects.get(project_lookup)
            return request.user.has_project_permission("CREATE_ENVIRONMENT", project)

        except Project.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin(obj.project.organisation):
            return True

        if request.user.is_environment_admin(obj):
            return True

        if request.user.is_project_admin(obj.project):
            return True

        if view.action == "user_permissions":
            return True
        return False


class IdentityPermissions(BasePermission):
    def has_permission(self, request, view):
        try:
            if view.action == "create":
                environment_api_key = view.kwargs.get("environment_api_key")
                environment = Environment.objects.get(api_key=environment_api_key)
                if not request.user.is_environment_admin(environment):
                    return False

            # return true as all users can list and specific object permissions will be handled later
            return view.detail

        except Environment.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin(obj.environment.project.organisation):
            return True

        if request.user.is_environment_admin(obj.environment):
            return True

        return False


class NestedEnvironmentPermissions(BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            environment_api_key = view.kwargs.get("environment_api_key")
            if not environment_api_key:
                return False

            environment = Environment.objects.get(api_key=environment_api_key)
            return request.user.is_environment_admin(environment)

        if view.action == "list":
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        if request.user.is_environment_admin(obj.environment):
            return True

        return False


class TraitPersistencePermissions(BasePermission):
    message = "Organisation is not authorised to store traits."

    def has_permission(self, request, view):
        # this permission class will only work when placed after
        # EnvironmentKeyPermissions class in a view
        return request.environment.project.organisation.persist_trait_data

    def has_object_permission(self, request, view, obj):
        # no views that use this permission currently have any detail endpoints
        return False


class EnvironmentAdminPermission(BasePermission):
    def has_permission(self, request, view):
        try:
            environment = Environment.objects.get(
                api_key=view.kwargs.get("environment_api_key")
            )
            return request.user.is_environment_admin(environment)
        except Environment.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        return request.user.is_environment_admin(obj.environment)


class HasEnvironmentPermission(BasePermission):
    def __init__(
        self,
        permission: str,
        environment: Environment,
    ):
        self._permission = permission
        self._environment = environment

    def has_permission(self, request, view):
        return request.user.has_environment_permission(
            self._permission, self._environment
        )

    def has_object_permission(self, request, view, obj):
        return request.user.has_environment_permission(
            self._permission, self._environment
        )

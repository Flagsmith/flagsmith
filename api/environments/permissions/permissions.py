import typing

from common.environments.permissions import VIEW_ENVIRONMENT  # type: ignore[import-untyped]
from common.projects.permissions import CREATE_ENVIRONMENT  # type: ignore[import-untyped]
from django.db.models import Model, Q
from rest_framework import exceptions
from rest_framework.permissions import BasePermission, IsAuthenticated

from environments.models import Environment
from projects.models import Project


class EnvironmentKeyPermissions(BasePermission):
    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        # Authentication class will set the environment on the request if it exists
        if hasattr(request, "environment"):
            return True

        raise exceptions.PermissionDenied("Missing or invalid Environment Key")

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        """
        This method is only called if has_permission returns true so we can safely return true for all requests here.
        """
        return True


class EnvironmentPermissions(IsAuthenticated):
    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        if not super().has_permission(request, view):
            return False

        if view.action == "create":
            try:
                project_id = request.data.get("project")
                project_lookup = Q(id=project_id)
                project = Project.objects.get(project_lookup)
                return request.user.has_project_permission(CREATE_ENVIRONMENT, project)
            except Project.DoesNotExist:
                return False

        # return true as all users can list and obj permissions will be handled later
        return True

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        if view.action == "clone":
            return request.user.has_project_permission(CREATE_ENVIRONMENT, obj.project)
        elif view.action in ("get_document", "retrieve", "trait_keys"):
            return request.user.has_environment_permission(VIEW_ENVIRONMENT, obj)

        return request.user.is_environment_admin(obj) or view.action in [
            "user_permissions"
        ]


class IdentityPermissions(BasePermission):
    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
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

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        if request.user.is_organisation_admin(obj.environment.project.organisation):
            return True

        if request.user.is_environment_admin(obj.environment):
            return True

        return False


class NestedEnvironmentPermissions(BasePermission):
    def __init__(  # type: ignore[no-untyped-def]
        self,
        *args,
        action_permission_map: typing.Dict[str, str] = None,  # type: ignore[assignment]
        get_environment_from_object_callable: typing.Callable[
            [Model], Environment
        ] = lambda o: o.environment,  # type: ignore[attr-defined]
        admin_actions: typing.Iterable[str] = None,  # type: ignore[assignment]
        **kwargs,
    ):
        super(NestedEnvironmentPermissions, self).__init__(*args, **kwargs)

        self.action_permission_map = action_permission_map or {}
        self.action_permission_map.setdefault("list", VIEW_ENVIRONMENT)

        self.get_environment_from_object_callable = get_environment_from_object_callable

    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        try:
            environment_api_key = view.kwargs.get("environment_api_key")
            environment = Environment.objects.get(api_key=environment_api_key)
        except Environment.DoesNotExist:
            return False

        if view.action in self.action_permission_map:
            return request.user.has_environment_permission(
                self.action_permission_map[view.action], environment
            )
        elif view.action == "create":
            # default to always allow environment admins to create
            return request.user.is_environment_admin(environment)

        return view.detail

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        if view.action in self.action_permission_map:
            return request.user.has_environment_permission(
                self.action_permission_map[view.action],
                self.get_environment_from_object_callable(obj),
            )

        return request.user.is_environment_admin(
            self.get_environment_from_object_callable(obj)
        )


class TraitPersistencePermissions(BasePermission):
    message = "Organisation is not authorised to store traits."

    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        # this permission class will only work when placed after
        # EnvironmentKeyPermissions class in a view
        return request.environment.project.organisation.persist_trait_data

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        # no views that use this permission currently have any detail endpoints
        return False


class EnvironmentAdminPermission(BasePermission):
    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        try:
            environment = Environment.objects.get(
                api_key=view.kwargs.get("environment_api_key")
            )
            return request.user.is_environment_admin(environment)
        except Environment.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        return request.user.is_environment_admin(obj.environment)

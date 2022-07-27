import typing

from django.db.models import Model
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.permissions import BasePermission

from organisations.models import Organisation
from organisations.permissions.permissions import CREATE_PROJECT
from projects.models import Project

# Maintain a list of permissions here
PROJECT_PERMISSIONS = [
    ("VIEW_PROJECT", "View permission for the given project."),
    ("CREATE_ENVIRONMENT", "Ability to create an environment in the given project."),
    ("DELETE_FEATURE", "Ability to delete features in the given project."),
    ("CREATE_FEATURE", "Ability to create features in the given project."),
    ("EDIT_FEATURE", "Ability to edit features in the given project."),
    ("MANAGE_SEGMENTS", "Ability to manage segments in the given project."),
]


class ProjectPermissions(BasePermission):
    def has_permission(self, request, view):
        """Check if user has permission to list / create project"""
        if view.action == "create" and request.user.belongs_to(
            int(request.data.get("organisation"))
        ):
            organisation = Organisation.objects.get(
                id=int(request.data.get("organisation"))
            )
            if organisation.restrict_project_create_to_admin:
                return request.user.is_organisation_admin(organisation.pk)
            return request.user.has_organisation_permission(
                organisation, CREATE_PROJECT
            )

        if view.action in ("list", "permissions"):
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to view / edit / delete project"""
        if request.user.is_project_admin(obj):
            return True

        if view.action == "retrieve" and request.user.has_project_permission(
            "VIEW_PROJECT", obj
        ):
            return True

        if view.action in ("update", "destroy") and request.user.is_project_admin(obj):
            return True

        if view.action == "user_permissions":
            return True

        return False


class IsProjectAdmin(BasePermission):
    def __init__(
        self,
        *args,
        project_pk_view_kwarg_attribute_name: str = "project_pk",
        get_project_from_object_callable: typing.Callable[
            [Model], Project
        ] = lambda o: o.project,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._view_kwarg_name = project_pk_view_kwarg_attribute_name
        self._get_project_from_object_callable = get_project_from_object_callable

    def has_permission(self, request, view):
        return request.user.is_project_admin(self._get_project(view)) or view.detail

    def has_object_permission(self, request, view, obj):
        return request.user.is_project_admin(
            self._get_project_from_object_callable(obj)
        )

    def _get_project(self, view) -> Project:
        try:
            project_pk = view.kwargs[self._view_kwarg_name]
            return Project.objects.get(id=project_pk)
        except KeyError:
            raise APIException(
                "`IsProjectAdmin` incorrectly configured. No project pk found."
            )
        except Project.DoesNotExist:
            raise PermissionDenied()


class NestedProjectPermissions(BasePermission):
    def __init__(
        self,
        *args,
        action_permission_map: typing.Dict[str, str] = None,
        get_project_from_object_callable: typing.Callable[
            [Model], Project
        ] = lambda o: o.environment,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.action_permission_map = action_permission_map or {}
        self.action_permission_map.setdefault("list", "VIEW_PROJECT")

        self.get_project_from_object_callable = get_project_from_object_callable

    def has_permission(self, request, view):
        try:
            environment_api_key = view.kwargs.get("project_pk")
            environment = Project.objects.get(api_key=environment_api_key)
        except Project.DoesNotExist:
            return False

        if view.action in self.action_permission_map:
            return request.user.has_project_permission(
                self.action_permission_map[view.action], environment
            )

        return view.detail

    def has_object_permission(self, request, view, obj):
        if view.action in self.action_permission_map:
            return request.user.has_environment_permission(
                self.action_permission_map[view.action],
                self.get_project_from_object_callable(obj),
            )

        return request.user.is_project_admin(self.get_project_from_object_callable(obj))

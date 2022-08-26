import typing

from django.db.models import Model
from django.http import HttpRequest
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated

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


class ProjectPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        """Check if user has permission to list / create project"""
        if not super().has_permission(request, view):
            return False

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
        if request.user.is_anonymous:
            return False

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


class MasterAPIKeyProjectPermissions(BasePermission):
    def has_permission(self, request: HttpRequest, view: str) -> bool:
        master_api_key = getattr(request, "master_api_key", None)

        if not master_api_key:
            return False

        if view.action == "create":
            organisation = int(request.data.get("organisation"))
            return organisation == master_api_key.organisation_id

        if view.action in ("list", "permissions"):
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(
        self, request: HttpRequest, view: str, obj: Project
    ) -> bool:
        master_api_key = request.master_api_key
        return master_api_key.organisation_id == obj.organisation.id


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
        ] = lambda o: o.project,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.action_permission_map = action_permission_map or {}
        self.action_permission_map.setdefault("list", "VIEW_PROJECT")

        self.get_project_from_object_callable = get_project_from_object_callable

    def has_permission(self, request, view):
        try:
            pk = view.kwargs.get("project_pk")
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return False

        if view.action in self.action_permission_map:
            return request.user.has_project_permission(
                self.action_permission_map[view.action], project
            )

        return view.detail

    def has_object_permission(self, request, view, obj):
        if view.action in self.action_permission_map:
            return request.user.has_project_permission(
                self.action_permission_map[view.action],
                self.get_project_from_object_callable(obj),
            )

        return request.user.is_project_admin(self.get_project_from_object_callable(obj))

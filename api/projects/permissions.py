import typing

from django.db.models import Model
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated

from organisations.models import Organisation
from organisations.permissions.permissions import CREATE_PROJECT
from projects.models import Project

VIEW_AUDIT_LOG = "VIEW_AUDIT_LOG"

# Maintain a list of permissions here
VIEW_PROJECT = "VIEW_PROJECT"
CREATE_ENVIRONMENT = "CREATE_ENVIRONMENT"
DELETE_FEATURE = "DELETE_FEATURE"
CREATE_FEATURE = "CREATE_FEATURE"
EDIT_FEATURE = "EDIT_FEATURE"
MANAGE_SEGMENTS = "MANAGE_SEGMENTS"

TAG_SUPPORTED_PERMISSIONS = [DELETE_FEATURE]

PROJECT_PERMISSIONS = [
    (VIEW_PROJECT, "View permission for the given project."),
    (CREATE_ENVIRONMENT, "Ability to create an environment in the given project."),
    (DELETE_FEATURE, "Ability to delete features in the given project."),
    (CREATE_FEATURE, "Ability to create features in the given project."),
    (EDIT_FEATURE, "Ability to edit features in the given project."),
    (MANAGE_SEGMENTS, "Ability to manage segments in the given project."),
    (VIEW_AUDIT_LOG, "Allows the user to view the audit logs for this organisation."),
]


class ProjectPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        """Check if user has permission to list / create project"""
        if not super().has_permission(request, view):
            return False

        if view.action == "create" and request.user.belongs_to(
            int(request.data.get("organisation"))
        ):
            organisation = Organisation.objects.select_related("subscription").get(
                id=int(request.data.get("organisation"))
            )

            # Allow project creation based on the active subscription
            subscription_metadata = (
                organisation.subscription.get_subscription_metadata()
            )
            total_projects_created = Project.objects.filter(
                organisation=organisation
            ).count()
            if (
                subscription_metadata.projects
                and total_projects_created >= subscription_metadata.projects
            ):
                return False
            if organisation.restrict_project_create_to_admin:
                return request.user.is_organisation_admin(organisation.pk)
            return request.user.has_organisation_permission(
                organisation, CREATE_PROJECT
            )
        if view.action in ("list", "permissions", "get_by_uuid"):
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        """Check if user has permission to view / edit / delete project"""
        if request.user.is_project_admin(obj):
            return True

        if view.action == "retrieve" and request.user.has_project_permission(
            VIEW_PROJECT, obj
        ):
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


class NestedProjectPermissions(IsAuthenticated):
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
        self.action_permission_map.setdefault("list", VIEW_PROJECT)

        self.get_project_from_object_callable = get_project_from_object_callable

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

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

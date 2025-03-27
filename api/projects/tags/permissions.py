from common.projects.permissions import (
    MANAGE_TAGS,
    VIEW_PROJECT,
)
from rest_framework.permissions import BasePermission

from projects.models import Project


class TagPermissions(BasePermission):
    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        project_pk = view.kwargs.get("project_pk")
        if not project_pk:
            return False
        project = Project.objects.get(pk=project_pk)

        permission = (
            VIEW_PROJECT if view.action in ("list", "get_by_uuid") else MANAGE_TAGS
        )
        return request.user.has_project_permission(permission, project) or view.detail

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        project = obj.project
        if request.user.has_project_permission(MANAGE_TAGS, obj.project):
            return True

        return view.action == "detail" and request.user.has_project_permission(
            VIEW_PROJECT, project
        )

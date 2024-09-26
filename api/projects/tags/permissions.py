from rest_framework.permissions import BasePermission

from projects.models import Project
from projects.permissions import MANAGE_TAGS, VIEW_PROJECT


class TagPermissions(BasePermission):
    def has_permission(self, request, view):
        project_pk = view.kwargs.get("project_pk")
        if not project_pk:
            return False
        project = Project.objects.get(pk=project_pk)

        if request.user.is_project_admin(project):
            return True

        if view.action in ["list", "get_by_uuid"]:
            return request.user.has_project_permission(VIEW_PROJECT, project)

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        project = obj.project
        if request.user.has_project_permission(MANAGE_TAGS, obj.project):
            return True

        return view.action == "detail" and request.user.has_project_permission(
            VIEW_PROJECT, project
        )

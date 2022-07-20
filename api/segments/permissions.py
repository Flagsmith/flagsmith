from rest_framework.permissions import BasePermission

from projects.models import Project


class SegmentPermissions(BasePermission):
    def has_permission(self, request, view):
        project_pk = view.kwargs.get("project_pk")
        if not project_pk:
            return False

        project = Project.objects.get(pk=project_pk)

        if request.user.has_project_permission("MANAGE_SEGMENTS", project):
            return True

        if view.action == "list" and request.user.has_project_permission(
            "VIEW_PROJECT", project
        ):
            # users with VIEW_PROJECT permission can list segments
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        return request.user.has_project_permission("MANAGE_SEGMENTS", obj.project) or (
            view.action == "detail"
            and request.user.has_project_permission("VIEW_PROJECT", obj.project)
        )

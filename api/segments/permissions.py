from rest_framework.permissions import IsAuthenticated

from projects.models import Project
from projects.permissions import MANAGE_SEGMENTS, VIEW_PROJECT


class SegmentPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        project_pk = view.kwargs.get("project_pk")
        if not project_pk:
            return False

        project = Project.objects.select_related("organisation").get(pk=project_pk)

        if request.user.has_project_permission(MANAGE_SEGMENTS, project):
            return True

        if view.action == "list" and request.user.has_project_permission(
            VIEW_PROJECT, project
        ):
            # users with VIEW_PROJECT permission can list segments
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        return request.user.has_project_permission(MANAGE_SEGMENTS, obj.project) or (
            view.action == "retrieve"
            and request.user.has_project_permission(VIEW_PROJECT, obj.project)
        )

from django.http import HttpRequest
from rest_framework.permissions import BasePermission, IsAuthenticated

from projects.models import Project
from projects.permissions import MANAGE_SEGMENTS, VIEW_PROJECT

from .models import Segment


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
        if request.user.is_anonymous:
            return False

        return request.user.has_project_permission(MANAGE_SEGMENTS, obj.project) or (
            view.action == "retrieve"
            and request.user.has_project_permission(VIEW_PROJECT, obj.project)
        )


class MasterAPIKeySegmentPermissions(BasePermission):
    def has_permission(self, request: HttpRequest, view: str) -> bool:
        master_api_key = getattr(request, "master_api_key", None)

        if not master_api_key:
            return False

        project_pk = view.kwargs.get("project_pk")
        if not project_pk:
            return False

        project = Project.objects.get(pk=project_pk)

        return project.organisation_id == master_api_key.organisation_id

    def has_object_permission(
        self, request: HttpRequest, view: str, obj: Segment
    ) -> bool:
        master_api_key = getattr(request, "master_api_key", None)
        return (
            master_api_key
            and master_api_key.organisation_id == obj.project.organisation_id
        )

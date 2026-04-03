from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from projects.models import Project


class HasPermissionToGitLabConfiguration(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        project_pk = view.kwargs.get("project_pk")
        try:
            project = Project.objects.get(id=project_pk)
        except Project.DoesNotExist:
            return False
        return bool(request.user.belongs_to(organisation_id=project.organisation_id))  # type: ignore[union-attr]

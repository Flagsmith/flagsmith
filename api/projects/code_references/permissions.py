from common.projects.permissions import VIEW_PROJECT
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from projects.models import Project
from users.models import FFAdminUser


class SubmitCodeReferences(IsAuthenticated):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not super().has_permission(request, view):
            return False

        if not (project_id := view.kwargs.get("project_pk")):
            return False

        if not isinstance(request.user, FFAdminUser):
            return False

        project = Project.objects.get(id=project_id)
        return request.user.has_project_permission(VIEW_PROJECT, project)

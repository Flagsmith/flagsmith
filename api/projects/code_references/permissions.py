from common.projects.permissions import VIEW_PROJECT
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from projects.models import Project
from users.models import FFAdminUser


class _BaseCodeReferencePermission(IsAuthenticated):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not super().has_permission(request, view):
            return False

        if not isinstance(request.user, FFAdminUser):  # pragma: no cover
            return False

        project = Project.objects.get(id=view.kwargs["project_pk"])
        return request.user.has_project_permission(VIEW_PROJECT, project)


class SubmitFeatureFlagCodeReferences(_BaseCodeReferencePermission):
    pass


class ViewFeatureFlagCodeReferences(_BaseCodeReferencePermission):
    pass

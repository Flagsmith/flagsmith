from common.projects.permissions import VIEW_PROJECT
from django.contrib.auth.models import AnonymousUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from projects.models import Project


class _BaseCodeReferencePermission(IsAuthenticated):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not super().has_permission(request, view):
            return False
        assert not isinstance(request.user, AnonymousUser)

        project = Project.objects.get(id=view.kwargs["project_pk"])
        return request.user.has_project_permission(VIEW_PROJECT, project)  # type: ignore[no-any-return]


class SubmitFeatureFlagCodeReferences(_BaseCodeReferencePermission):
    pass


class ViewFeatureFlagCodeReferences(_BaseCodeReferencePermission):
    pass

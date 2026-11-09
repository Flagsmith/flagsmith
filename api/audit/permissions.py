from common.projects.permissions import VIEW_AUDIT_LOG
from django.contrib.auth.models import AnonymousUser
from django.views import View
from rest_framework.exceptions import NotFound
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from organisations.models import Organisation
from projects.models import Project


class OrganisationAuditLogPermissions(BasePermission):
    def has_permission(self, request: Request, view: View):  # type: ignore[no-untyped-def]
        try:
            organisation_id = view.kwargs["organisation_pk"]
            organisation = Organisation.objects.get(id=organisation_id)
        except (Organisation.DoesNotExist, KeyError):
            return False

        user = request.user
        assert not isinstance(user, AnonymousUser)
        if user.is_organisation_admin(organisation):
            return True
        if not user.belongs_to(organisation.id):
            raise NotFound()
        return False


class ProjectAuditLogPermissions(BasePermission):
    def has_permission(self, request: Request, view: View):  # type: ignore[no-untyped-def]
        try:
            project_id = view.kwargs["project_pk"]
            project = Project.objects.get(id=project_id)
        except (Project.DoesNotExist, KeyError):
            return False

        return request.user.has_project_permission(VIEW_AUDIT_LOG, project)  # type: ignore[union-attr]

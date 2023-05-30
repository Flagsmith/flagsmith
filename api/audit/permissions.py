from django.views import View
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from organisations.models import Organisation
from organisations.permissions.permissions import VIEW_AUDIT_LOG
from projects.models import Project


class OrganisationAuditLogPermissions(BasePermission):
    def has_permission(self, request: Request, view: View):
        try:
            organisation_id = view.kwargs["organisation_pk"]
            organisation = Organisation.objects.get(id=organisation_id)
        except (Organisation.DoesNotExist, KeyError):
            return False

        return request.user.has_organisation_permission(organisation, VIEW_AUDIT_LOG)


class ProjectAuditLogPermissions(BasePermission):
    def has_permission(self, request: Request, view: View):
        try:
            project_id = view.kwargs["project_pk"]
            project = Project.objects.get(id=project_id)
        except (Project.DoesNotExist, KeyError):
            return False

        return request.user.has_project_permission(VIEW_AUDIT_LOG, project)

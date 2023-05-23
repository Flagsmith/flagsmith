from django.views import View
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from organisations.models import Organisation
from organisations.permissions.permissions import VIEW_AUDIT_LOG


class OrganisationAuditLogPermissions(BasePermission):
    def has_permission(self, request: Request, view: View):
        try:
            organisation_id = view.kwargs["organisation_pk"]
            organisation = Organisation.objects.get(id=organisation_id)
        except (Organisation.DoesNotExist, KeyError):
            return False

        return request.user.has_organisation_permission(organisation, VIEW_AUDIT_LOG)

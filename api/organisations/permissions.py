from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from organisations.models import Organisation


class NestedOrganisationEntityPermission(BasePermission):
    def has_permission(self, request, view):
        organisation_pk = view.kwargs.get("organisation_pk")
        if organisation_pk and request.user.is_admin(
            Organisation.objects.get(pk=organisation_pk)
        ):
            return True

        raise PermissionDenied(
            "User does not have sufficient privileges to perform this action"
        )

    def has_object_permission(self, request, view, obj):
        organisation_id = view.kwargs.get("organisation_pk")
        organisation = Organisation.objects.get(id=organisation_id)

        if request.user.is_admin(organisation):
            return True

        return False


class OrganisationPermission(BasePermission):
    def has_permission(self, request, view):
        if (
            view.action == "create"
            and settings.ONLY_SUPERUSERS_CAN_CREATE_ORGANISATIONS
        ):
            return request.user.is_superuser
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin(obj):
            return True

        raise PermissionDenied(
            "User does not have sufficient privileges to perform this action"
        )


class OrganisationUsersPermission(BasePermission):
    def has_permission(self, request, view):
        organisation_id = view.kwargs.get("organisation_pk")
        organisation = Organisation.objects.get(id=organisation_id)

        if request.user.is_admin(organisation):
            return True

        if view.action == "list" and request.user.belongs_to(organisation.id):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        organisation_id = view.kwargs.get("organisation_pk")
        organisation = Organisation.objects.get(id=organisation_id)

        if request.user.is_admin(organisation):
            return True

        return False


class UserPermissionGroupPermission(BasePermission):
    def has_permission(self, request, view):
        organisation_pk = view.kwargs.get("organisation_pk")
        if organisation_pk and request.user.is_admin(
            Organisation.objects.get(pk=organisation_pk)
        ):
            return True

        if view.action == "list" and request.user.belongs_to(int(organisation_pk)):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        organisation_id = view.kwargs.get("organisation_pk")
        organisation = Organisation.objects.get(id=organisation_id)

        if request.user.is_admin(organisation):
            return True

        return False

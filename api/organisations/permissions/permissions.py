import typing
from contextlib import suppress

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from organisations.models import Organisation

CREATE_PROJECT = "CREATE_PROJECT"

ORGANISATION_PERMISSIONS = (
    (CREATE_PROJECT, "Allows the user to create projects in this organisation."),
)


class NestedOrganisationEntityPermission(BasePermission):
    def has_permission(self, request, view):
        organisation_pk = view.kwargs.get("organisation_pk")
        if organisation_pk and request.user.is_organisation_admin(
            Organisation.objects.get(pk=organisation_pk)
        ):
            return True

        raise PermissionDenied(
            "User does not have sufficient privileges to perform this action"
        )

    def has_object_permission(self, request, view, obj):
        organisation_id = view.kwargs.get("organisation_pk")
        organisation = Organisation.objects.get(id=organisation_id)
        return request.user.is_organisation_admin(organisation)


class OrganisationPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == "create" and settings.RESTRICT_ORG_CREATE_TO_SUPERUSERS:
            return request.user.is_superuser
        return True

    def has_object_permission(self, request, view, obj):
        if request.user.is_organisation_admin(obj) or (
            view.action == "my_permissions" and obj in request.user.organisations.all()
        ):
            return True

        raise PermissionDenied(
            "User does not have sufficient privileges to perform this action"
        )


class OrganisationUsersPermission(BasePermission):
    def has_permission(self, request, view):
        organisation_id = view.kwargs.get("organisation_pk")
        organisation = Organisation.objects.get(id=organisation_id)

        if request.user.is_organisation_admin(organisation):
            return True

        if view.action == "list" and request.user.belongs_to(organisation.id):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        organisation_id = view.kwargs.get("organisation_pk")
        organisation = Organisation.objects.get(id=organisation_id)

        if request.user.is_organisation_admin(organisation):
            return True

        return False


class UserPermissionGroupPermission(BasePermission):
    def has_permission(self, request, view):
        organisation_pk = view.kwargs.get("organisation_pk")
        if organisation_pk and request.user.is_organisation_admin(
            Organisation.objects.get(pk=organisation_pk)
        ):
            return True

        if view.action == "list" and request.user.belongs_to(int(organisation_pk)):
            return True

        return False

    def has_object_permission(self, request, view, obj):
        organisation_id = view.kwargs.get("organisation_pk")
        organisation = Organisation.objects.get(id=organisation_id)

        if request.user.is_organisation_admin(organisation):
            return True

        return False


class NestedIsOrganisationAdminPermission(BasePermission):
    def __init__(
        self,
        *args,
        get_organisation_from_object_callable: typing.Callable[
            [Model], Organisation
        ] = lambda o: o.organisation,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.get_organisation_from_object_callable = (
            get_organisation_from_object_callable
        )

    def has_permission(self, request, view):
        organisation_pk = view.kwargs.get("organisation_pk")

        with suppress(ObjectDoesNotExist):
            return request.user.is_organisation_admin(
                Organisation.objects.get(pk=organisation_pk)
            )
        return False

    def has_object_permission(self, request, view, obj):
        return request.user.is_organisation_admin(
            self.get_organisation_from_object_callable(obj)
        )

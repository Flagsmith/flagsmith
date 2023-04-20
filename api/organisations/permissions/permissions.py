import typing
from contextlib import suppress

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.views import View
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from organisations.models import Organisation

CREATE_PROJECT = "CREATE_PROJECT"
MANAGE_USER_GROUPS = "MANAGE_USER_GROUPS"

ORGANISATION_PERMISSIONS = (
    (CREATE_PROJECT, "Allows the user to create projects in this organisation."),
    (
        MANAGE_USER_GROUPS,
        "Allows the user to manage the groups in the organisation and their members.",
    ),
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


class HasOrganisationPermission(BasePermission):
    def __init__(
        self,
        *args,
        permission_key: str,
        get_organisation_pk_from_view_callable: typing.Callable[
            [View], int
        ] = lambda v: v.kwargs.get("organisation_pk"),
        get_organisation_from_object_callable: typing.Callable[
            [Model], Organisation
        ] = lambda o: o.organisation,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.permission_key = permission_key
        self.get_organisation_from_object_callable = (
            get_organisation_from_object_callable
        )
        self.get_organisation_pk_from_view_callable = (
            get_organisation_pk_from_view_callable
        )

    def has_permission(self, request, view):
        try:
            organisation_pk = self.get_organisation_pk_from_view_callable(view)
            organisation = Organisation.objects.get(pk=organisation_pk)
        except Organisation.DoesNotExist:
            return False

        return request.user.has_organisation_permission(
            organisation=organisation, permission_key=self.permission_key
        )

    def has_object_permission(self, request, view, obj):
        organisation = self.get_organisation_from_object_callable(obj)
        organisation_pk = self.get_organisation_pk_from_view_callable(view)
        return (
            organisation_pk
            and organisation.id == int(organisation_pk)
            and self.has_permission(request, view)
        )


class OrganisationPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action == "create" and settings.RESTRICT_ORG_CREATE_TO_SUPERUSERS:
            return request.user.is_superuser
        return True

    def has_object_permission(self, request, view, obj):
        return request.user.is_organisation_admin(obj) or (
            view.action == "my_permissions" and obj in request.user.organisations.all()
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
        try:
            organisation_pk = view.kwargs.get("organisation_pk")
            organisation = Organisation.objects.get(pk=organisation_pk)
        except Organisation.DoesNotExist:
            return False

        return (
            (view.action == "list" and request.user.belongs_to(organisation.id))
            or view.detail is True  # delegate to has_object_permission
            or request.user.has_organisation_permission(
                organisation, MANAGE_USER_GROUPS
            )
        )

    def has_object_permission(self, request, view, obj):
        organisation_id = view.kwargs.get("organisation_pk")
        if request.user.is_group_admin(obj.id):
            return True

        organisation = Organisation.objects.get(id=organisation_id)
        return request.user.has_organisation_permission(
            organisation, MANAGE_USER_GROUPS
        )


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

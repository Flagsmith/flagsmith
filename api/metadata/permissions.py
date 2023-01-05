from contextlib import suppress

from rest_framework.permissions import IsAuthenticated

from metadata.models import MetadataField
from organisations.models import Organisation


class MetadataFieldPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        # list is handled by the view
        if view.action == "list" or view.detail:
            return True

        if view.action == "create":
            with suppress(Organisation.DoesNotExist):
                organisation_id = request.data.get("organisation")
                organisation = Organisation.objects.get(id=organisation_id)
                return request.user.is_organisation_admin(organisation)

        return False

    def has_object_permission(self, request, view, obj):
        if view.action in ("retrieve"):
            return request.user.belongs_to(obj.organisation.id)

        if view.action in (
            "update",
            "destroy",
            "partial_update",
        ):
            return request.user.is_organisation_admin(obj.organisation)

        return False


class MetadataModelFieldPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        with suppress(MetadataField.DoesNotExist, ValueError):
            organisation_pk = int(view.kwargs.get("organisation_pk"))

            if request.user.belongs_to(organisation_pk):
                if (
                    view.action
                    in [
                        "list",
                        "get_supported_content_types",
                        "get_supported_required_for_model",
                    ]
                    or view.detail
                ):
                    return True

                if view.action == "create":
                    field = MetadataField.objects.get(id=request.data.get("field"))

                    return (
                        request.user.is_organisation_admin(organisation_pk)
                        and organisation_pk == field.organisation.id
                    )

        return False

    def has_object_permission(self, request, view, obj):
        if view.action in ("retrieve"):
            return request.user.belongs_to(obj.field.organisation.id)

        if view.action in ("update", "destroy", "partial_update"):
            return request.user.is_organisation_admin(obj.field.organisation)

        return False

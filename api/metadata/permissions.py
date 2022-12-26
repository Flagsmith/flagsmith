from rest_framework.permissions import IsAuthenticated


class MetadataFieldPermissions(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        organisation = request.data.get("organisation")
        if view.action == "create" and request.user.belongs_to(organisation):
            return request.user.is_organisation_admin(request.data.get("organisation"))

        # list is handled by the view
        if view.action == "list":
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        if view.action in ("update", "destroy") and request.user.is_organisation_admin(
            obj.organisation
        ):
            return True

        return False

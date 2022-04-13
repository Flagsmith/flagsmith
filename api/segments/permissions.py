from rest_framework.permissions import BasePermission

from environments.identities.models import Identity
from projects.models import Project


class SegmentPermissions(BasePermission):
    def has_permission(self, request, view):
        project_pk = view.kwargs.get("project_pk")
        if not project_pk:
            return False

        project = Project.objects.get(pk=project_pk)
        organisation = project.organisation

        if request.user.is_project_admin(project) or request.user.is_organisation_admin(
            organisation
        ):
            return True

        # environment admins should be able to get segments for an identity
        if "identity" in request.query_params:
            identity = Identity.objects.get(pk=request.query_params["identity"])
            if request.user.is_environment_admin(identity.environment):
                return True

        if view.action == "list" and request.user.has_project_permission(
            "VIEW_PROJECT", project
        ):
            # users with VIEW_PROJECT permission can list segments
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        project = obj.project
        organisation = project.organisation
        return (
            request.user.is_project_admin(project)
            or request.user.is_organisation_admin(organisation)
            or (
                view.action == "detail"
                and request.user.has_project_permission("VIEW_PROJECT", project)
            )
        )

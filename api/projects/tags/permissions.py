from rest_framework.permissions import BasePermission

from projects.models import Project


class TagPermissions(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        project_pk = view.kwargs.get("project_pk")
        if not project_pk:
            return False

        project = Project.objects.get(pk=project_pk)
        organisation = project.organisation

        if user.is_project_admin(project) or user.is_organisation_admin(organisation):
            return True

        if view.action == "list" and request.user.has_project_permission(
            "VIEW_PROJECT", project
        ):
            return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        user = request.user
        project = obj.project
        organisation = project.organisation

        if user.is_project_admin(project) or user.is_organisation_admin(organisation):
            return True

        return view.action == "detail" and request.user.has_project_permission(
            "VIEW_PROJECT", project
        )

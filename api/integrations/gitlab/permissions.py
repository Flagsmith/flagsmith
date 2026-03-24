from rest_framework.permissions import BasePermission

from projects.models import Project


class HasPermissionToGitlabConfiguration(BasePermission):
    """
    Custom permission to only allow users with permission to access
    GitLabConfiguration related to their project's organisation.
    """

    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        project_pk = view.kwargs.get("project_pk")
        try:
            project = Project.objects.get(id=int(project_pk))
        except Project.DoesNotExist:
            return False
        return request.user.belongs_to(organisation_id=project.organisation_id)

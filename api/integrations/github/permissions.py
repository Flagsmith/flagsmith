from rest_framework.permissions import BasePermission


class HasPermissionToGithubConfiguration(BasePermission):
    """
    Custom permission to only allow users with permission to access
    GithubConfiguration related to their organisations.
    """

    def has_permission(self, request, view):

        organisation_id = view.kwargs.get("organisation_pk")

        return request.user.belongs_to(organisation_id=int(organisation_id))

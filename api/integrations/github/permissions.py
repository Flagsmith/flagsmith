from rest_framework.permissions import BasePermission

from users.models import FFAdminUser


class HasPermissionToGithubConfiguration(BasePermission):
    """
    Custom permission to only allow users with permission to access
    GithubConfiguration related to their organisations.
    """

    def has_permission(self, request, view):

        if isinstance(request.user, FFAdminUser):
            organisation_id = view.kwargs.get("organisation_pk")
            return request.user.belongs_to(organisation_id=organisation_id)
        else:
            return request.user.is_master_api_key_user

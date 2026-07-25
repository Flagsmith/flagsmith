from rest_framework.permissions import BasePermission

from integrations.github.models import GithubConfiguration


class HasPermissionToGithubConfiguration(BasePermission):
    """
    Custom permission to only allow users with permission to access
    GithubConfiguration related to their organisations.
    """

    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        organisation_id = view.kwargs.get("organisation_pk")

        if not request.user.belongs_to(organisation_id=int(organisation_id)):
            return False

        # For nested routes, ensure the GitHub configuration in the URL belongs
        # to the organisation the caller is authorised for
        if (github_pk := view.kwargs.get("github_pk")) is not None and str(
            github_pk
        ).isdigit():
            return GithubConfiguration.objects.filter(
                id=github_pk,
                organisation_id=organisation_id,
            ).exists()

        return True

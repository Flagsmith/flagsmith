from rest_framework.permissions import IsAuthenticated

from projects.models import Project

# NOTE: These constants should eventually be added to the flagsmith-common package
# (common.projects.permissions module). For now, they're defined here locally.
MANAGE_BUCKETS = "MANAGE_BUCKETS"
VIEW_BUCKET = "VIEW_BUCKET"


ACTION_PERMISSIONS_MAP = {
    "retrieve": VIEW_BUCKET,
    "list": VIEW_BUCKET,
    "create": MANAGE_BUCKETS,
    "update": MANAGE_BUCKETS,
    "partial_update": MANAGE_BUCKETS,
    "destroy": MANAGE_BUCKETS,
}


class BucketPermissions(IsAuthenticated):
    """
    Permission class for Bucket operations.

    - LIST/RETRIEVE: Requires VIEW_BUCKET permission on the project
    - CREATE/UPDATE/DELETE: Requires MANAGE_BUCKETS permission on the project
    """

    def has_permission(self, request, view):
        """Check if user has permission for list/create actions"""
        if not super().has_permission(request, view):
            return False

        # Object-level permissions handled by has_object_permission
        if view.detail:
            return True

        # For list and create actions, check project-level permissions
        if view.action in ["list", "create"]:
            try:
                project_id = view.kwargs.get("project_pk")
                project = Project.objects.get(id=project_id)

                required_permission = ACTION_PERMISSIONS_MAP.get(view.action)
                return request.user.has_project_permission(required_permission, project)
            except Project.DoesNotExist:
                return False

        return False

    def has_object_permission(self, request, view, obj):
        """Check if user has permission for retrieve/update/delete on specific bucket"""
        if view.action in ACTION_PERMISSIONS_MAP:
            required_permission = ACTION_PERMISSIONS_MAP[view.action]
            return request.user.has_project_permission(required_permission, obj.project)

        return False

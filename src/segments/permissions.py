from rest_framework.permissions import BasePermission

from environments.models import Identity
from projects.models import Project


class SegmentPermissions(BasePermission):
    def has_permission(self, request, view):
        project_pk = view.kwargs.get('project_pk')
        if not project_pk:
            return False

        project = Project.objects.get(pk=project_pk)

        if request.user.is_project_admin(project):
            return True

        # environment admins should be able to get segments for an identity
        if 'identity' in request.query_params:
            identity = Identity.objects.get(pk=request.query_params['identity'])
            if request.user.is_environment_admin(identity.environment):
                return True

        # move on to object specific permissions
        return view.detail

    def has_object_permission(self, request, view, obj):
        if request.user.is_project_admin(obj.project):
            return True

        return False
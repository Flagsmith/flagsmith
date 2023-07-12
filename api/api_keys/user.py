import typing

from django.db.models import QuerySet

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from projects.models import Project


class APIKeyUser:
    key = None

    def __init__(self, key):
        self.key = key

    def is_authenticated(self):
        return True

    def has_project_permission(self, permission: str, project: "Project") -> bool:
        # TODO: Implement this
        return True

    def has_environment_permission(
        self, permission: str, environment: "Environment"
    ) -> bool:
        # TODO: Implement this
        return True

    def get_permitted_projects(self, permission_key: str) -> QuerySet["Project"]:
        return None
        # return get_permitted_projects_for_user(self, permission_key)

    def get_permitted_environments(
        self, permission_key: str, project: "Project"
    ) -> QuerySet["Environment"]:
        return None
        # return get_permitted_environments_for_user(self, project, permission_key)

import typing

from django.db.models import QuerySet

from organisations.models import Organisation
from permissions.permission_service import (
    get_permitted_environments_for_master_api_key,
    get_permitted_projects_for_master_api_key,
    is_master_api_key_environment_admin,
    is_master_api_key_project_admin,
    master_api_key_has_organisation_permission,
)
from users.abc import UserABC

from .models import MasterAPIKey

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from projects.models import Project


class APIKeyUser(UserABC):
    def __init__(self, key: MasterAPIKey):
        self.key = key

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def pk(self) -> str:
        return self.key.id

    @property
    def is_master_api_key_user(self) -> bool:
        return True

    def belongs_to(self, organisation_id: int) -> bool:
        return self.key.organisation_id == organisation_id

    def is_project_admin(self, project: "Project") -> bool:
        return is_master_api_key_project_admin(self.key, project)

    def is_environment_admin(self, environment: "Environment") -> bool:
        return is_master_api_key_environment_admin(self.key, environment)

    def has_project_permission(self, permission: str, project: "Project") -> bool:
        return project in self.get_permitted_projects(permission)

    def has_environment_permission(
        self, permission: str, environment: "Environment"
    ) -> bool:
        return environment in self.get_permitted_environments(
            permission, environment.project
        )

    def has_organisation_permission(
        self, organisation: Organisation, permission_key: str
    ) -> bool:
        return master_api_key_has_organisation_permission(
            self.key, organisation, permission_key
        )

    def get_permitted_projects(self, permission_key: str) -> QuerySet["Project"]:
        return get_permitted_projects_for_master_api_key(self.key, permission_key)

    def get_permitted_environments(
        self, permission_key: str, project: "Project"
    ) -> QuerySet["Environment"]:
        return get_permitted_environments_for_master_api_key(
            self.key, project, permission_key
        )

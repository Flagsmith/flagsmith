import typing

from django.db.models import QuerySet

from organisations.models import Organisation, OrganisationRole
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

    @property
    def organisations(self) -> QuerySet[Organisation]:
        return Organisation.objects.filter(id=self.key.organisation_id)

    def belongs_to(self, organisation_id: int) -> bool:
        return self.key.organisation_id == organisation_id

    def is_organisation_admin(
        self, organisation: typing.Union["Organisation", int]
    ) -> bool:
        org_id = organisation.id if hasattr(organisation, "id") else organisation
        return self.key.is_admin and self.key.organisation_id == org_id

    def get_organisation_role(self, organisation: Organisation) -> typing.Optional[str]:
        if self.key.organisation_id != organisation.id:
            return None

        return (
            OrganisationRole.ADMIN.value
            if self.key.is_admin
            else OrganisationRole.USER.value
        )

    def is_project_admin(self, project: "Project") -> bool:
        return is_master_api_key_project_admin(self.key, project)

    def is_environment_admin(self, environment: "Environment") -> bool:
        return is_master_api_key_environment_admin(self.key, environment)

    def has_project_permission(
        self, permission: str, project: "Project", tag_ids: typing.List[int] = None
    ) -> bool:
        return project in self.get_permitted_projects(permission, tag_ids)

    def has_environment_permission(
        self,
        permission: str,
        environment: "Environment",
        tag_ids: typing.List[int] = None,
    ) -> bool:
        return environment in self.get_permitted_environments(
            permission, environment.project, tag_ids
        )

    def has_organisation_permission(
        self, organisation: Organisation, permission_key: str
    ) -> bool:
        return master_api_key_has_organisation_permission(
            self.key, organisation, permission_key
        )

    def get_permitted_projects(
        self, permission_key: str, tag_ids: typing.List[int] = None
    ) -> QuerySet["Project"]:
        return get_permitted_projects_for_master_api_key(
            self.key, permission_key, tag_ids
        )

    def get_permitted_environments(
        self,
        permission_key: str,
        project: "Project",
        tag_ids: typing.List[int] = None,
        prefetch_metadata: bool = False,
    ) -> QuerySet["Environment"]:
        return get_permitted_environments_for_master_api_key(
            self.key, project, permission_key, tag_ids, prefetch_metadata
        )

from abc import ABC, abstractmethod

from django.db.models import QuerySet

from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project


class UserABC(ABC):
    @property
    @abstractmethod
    def is_authenticated(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def belongs_to(self, organisation_id: int) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def is_project_admin(self, project: "Project") -> bool:
        raise NotImplementedError()

    @abstractmethod
    def is_environment_admin(self, environment: "Environment") -> bool:
        raise NotImplementedError()

    @abstractmethod
    def has_project_permission(self, permission: str, project: "Project") -> bool:
        raise NotImplementedError()

    @abstractmethod
    def has_environment_permission(
        self, permission: str, environment: "Environment"
    ) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def has_organisation_permission(
        self, organisation: Organisation, permission_key: str
    ) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_permitted_projects(self, permission_key: str) -> QuerySet["Project"]:
        raise NotImplementedError()

    @abstractmethod
    def get_permitted_environments(
        self, permission_key: str, project: "Project"
    ) -> QuerySet["Environment"]:
        raise NotImplementedError()

    @classmethod
    def __subclasshook__(cls, subclass):
        return all([hasattr(subclass, attr) for attr in cls.__abstractmethods__])

import abc
import typing

from users.models import FFAdminUser


class LeadTracker(abc.ABC):
    def __init__(self, client: typing.Any = None):
        self.client = client or self._get_client()

    @staticmethod
    @abc.abstractmethod
    def should_track(user: FFAdminUser) -> bool:
        pass

    @abc.abstractmethod
    def create_lead(self, user: FFAdminUser):
        pass

    @abc.abstractmethod
    def _get_client(self) -> typing.Any:
        pass

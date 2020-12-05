from abc import ABC, abstractmethod, abstractstaticmethod

from util.util import postpone


class AbstractBaseEventIntegrationWrapper(ABC):
    @abstractmethod
    def _track_event(self, event: dict) -> None:
        raise NotImplementedError

    @postpone
    def track_event_async(self, event: dict) -> None:
        self._track_event(event)

    @abstractstaticmethod
    def generate_event_data(*args, **kwargs) -> None:
        raise NotImplementedError

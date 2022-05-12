import typing
from abc import ABC, abstractmethod, abstractstaticmethod

from util.util import postpone

if typing.TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from features.models import FeatureState


class AbstractBaseEventIntegrationWrapper(ABC):
    @abstractmethod
    def _track_event(self, event: dict) -> None:
        raise NotImplementedError()

    @postpone
    def track_event_async(self, event: dict) -> None:
        self._track_event(event)

    @abstractstaticmethod
    def generate_event_data(*args, **kwargs) -> None:
        raise NotImplementedError()


class AbstractBaseIdentityIntegrationWrapper(ABC):
    @abstractmethod
    def _identify_user(self, user_data: dict) -> None:
        raise NotImplementedError()

    @postpone
    def identify_user_async(self, data: dict) -> None:
        self._identify_user(data)

    @abstractmethod
    def generate_user_data(
        self,
        identity: "Identity",
        feature_states: typing.List["FeatureState"],
        trait_models: typing.List["Trait"],
    ) -> dict:
        raise NotImplementedError()

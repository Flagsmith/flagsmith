import typing
from abc import ABC, abstractmethod

from util.util import postpone

if typing.TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from features.models import FeatureState


T = typing.TypeVar("T")


class AbstractBaseEventIntegrationWrapper(ABC):
    @abstractmethod
    def _track_event(self, event: dict) -> None:  # type: ignore[type-arg]
        raise NotImplementedError()

    @postpone  # type: ignore[misc]
    def track_event_async(self, event: dict) -> None:  # type: ignore[type-arg]
        self._track_event(event)

    @staticmethod
    @abstractmethod
    def generate_event_data(*args, **kwargs) -> ...:  # type: ignore[misc,no-untyped-def]
        raise NotImplementedError()


class AbstractBaseIdentityIntegrationWrapper(ABC, typing.Generic[T]):
    @abstractmethod
    def _identify_user(self, user_data: T) -> None:
        raise NotImplementedError()

    @postpone  # type: ignore[misc]
    def identify_user_async(self, data: T) -> None:
        self._identify_user(data)

    @abstractmethod
    def generate_user_data(
        self,
        identity: "Identity",
        feature_states: typing.List["FeatureState"],
        trait_models: typing.List["Trait"],
    ) -> T:
        raise NotImplementedError()

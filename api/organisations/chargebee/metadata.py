from enum import Enum

from organisations.subscriptions.constants import CHARGEBEE
from organisations.subscriptions.metadata import BaseSubscriptionMetadata


class ChargebeeObjMetadata(BaseSubscriptionMetadata):
    payment_source = CHARGEBEE  # type: ignore[assignment]

    def __mul__(self, other):  # type: ignore[no-untyped-def]
        if not isinstance(other, int):
            raise TypeError("Unable to multiply by anything other than an integer.")

        return ChargebeeObjMetadata(
            **{k: v * other if v else v for k, v in self.__dict__.items()}
        )


class ChargebeeItem(Enum):
    PLAN = "Plan"
    ADDON = "Addon"

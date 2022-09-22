from dataclasses import dataclass
from enum import Enum

from organisations.subscriptions.constants import CHARGEBEE
from organisations.subscriptions.dataclasses import BaseSubscriptionMetadata


@dataclass
class ChargebeeObjMetadata(BaseSubscriptionMetadata):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment_source = CHARGEBEE

    def __mul__(self, other):
        if not isinstance(other, int):
            raise TypeError("Unable to multiply by anything other than an integer.")

        return ChargebeeObjMetadata(
            **{k: v * other if v else v for k, v in self.__dict__.items()}
        )


class ChargebeeItem(Enum):
    PLAN = "Plan"
    ADDON = "Addon"

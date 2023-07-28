import typing
from enum import Enum

from organisations.subscriptions.constants import CHARGEBEE
from organisations.subscriptions.metadata import BaseSubscriptionMetadata


class ChargebeeObjMetadata(BaseSubscriptionMetadata):
    payment_source = CHARGEBEE

    def __mul__(self, other):
        if not isinstance(other, int):
            raise TypeError("Unable to multiply by anything other than an integer.")

        return ChargebeeObjMetadata(
            **{k: v * other if v else v for k, v in self.__dict__.items()}
        )


class ChargebeeItem(Enum):
    PLAN = "Plan"
    ADDON = "Addon"


class ChargebeePlanMetadata(ChargebeeObjMetadata):
    pass


class ChargebeeSubscriptionMetadata(ChargebeeObjMetadata):
    def __init__(
        self,
        seats: int = 0,
        api_calls: int = 0,
        projects: typing.Optional[int] = None,
        chargebee_email=None,
    ):
        self.chargebee_email = chargebee_email
        super(ChargebeeSubscriptionMetadata, self).__init__(seats, api_calls, projects)

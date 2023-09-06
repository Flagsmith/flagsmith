import typing
from enum import Enum

from organisations.subscriptions.constants import CHARGEBEE
from organisations.subscriptions.metadata import BaseSubscriptionMetadata


class ChargebeeObjMetadata(BaseSubscriptionMetadata):
    payment_source = CHARGEBEE

    def __mul__(self, other: int) -> "ChargebeeObjMetadata":
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


class ChargebeeAddOnMetadata(ChargebeeObjMetadata):
    pass


class ChargebeeSubscriptionMetadata(ChargebeeObjMetadata):
    def __init__(
        self,
        plan_id: str,
        chargebee_email: str,
        seats: int = 0,
        api_calls: int = 0,
        projects: typing.Optional[int] = None,
    ):
        self.plan_id = plan_id
        self.chargebee_email = chargebee_email
        super().__init__(seats, api_calls, projects)

    @classmethod
    def from_chargebee_plan_metadata(
        cls,
        plan_id: str,
        chargebee_email: str,
        chargebee_plan_metadata: ChargebeePlanMetadata,
    ) -> "ChargebeeSubscriptionMetadata":
        return cls(
            plan_id=plan_id,
            chargebee_email=chargebee_email,
            seats=chargebee_plan_metadata.seats,
            api_calls=chargebee_plan_metadata.api_calls,
            projects=chargebee_plan_metadata.projects,
        )

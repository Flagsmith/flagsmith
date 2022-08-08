from dataclasses import dataclass
from enum import Enum

from organisations.subscriptions.constants import CHARGEBEE
from organisations.subscriptions.dataclasses import BaseSubscriptionMetadata


@dataclass
class ChargebeeObjMetadata(BaseSubscriptionMetadata):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment_source = CHARGEBEE


class ChargebeeItem(Enum):
    PLAN = "Plan"
    ADDON = "Addon"

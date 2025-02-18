from typing import Literal

from . import constants

PERIOD_TYPE = Literal[  # type: ignore[valid-type]
    constants.CURRENT_BILLING_PERIOD,
    constants.PREVIOUS_BILLING_PERIOD,
    constants.NINETY_DAY_PERIOD,
]

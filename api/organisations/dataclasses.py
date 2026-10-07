from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class APILimitEnforcement:
    """
    Restrictions applied to a free organisation once its API limit
    grace period is over.
    """

    stops_serving_flags: bool
    blocks_access_to_admin: bool

    @property
    def enabled(self) -> bool:
        return self.stops_serving_flags or self.blocks_access_to_admin

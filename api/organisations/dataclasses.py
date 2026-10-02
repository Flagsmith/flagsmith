from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class APILimitRestrictions:
    stop_serving_flags: bool
    block_access_to_admin: bool

    @property
    def enabled(self) -> bool:
        return self.stop_serving_flags or self.block_access_to_admin

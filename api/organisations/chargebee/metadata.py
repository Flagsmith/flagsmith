from dataclasses import dataclass
from enum import Enum


@dataclass
class ChargebeeObjMetadata:
    seats: int = 0
    api_calls: int = 0
    projects: int = 0

    def __add__(self, other):
        return ChargebeeObjMetadata(
            seats=self.seats + other.seats,
            api_calls=self.api_calls + other.api_calls,
            projects=self.projects + other.projects,
        )


class ChargebeeItem(Enum):
    PLAN = "Plan"
    ADDON = "Addon"

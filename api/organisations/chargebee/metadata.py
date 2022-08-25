import typing
from dataclasses import dataclass
from enum import Enum


@dataclass
class ChargebeeObjMetadata:
    seats: int = 0
    api_calls: int = 0
    projects: typing.Optional[int] = 0

    def __add__(self, other):
        return ChargebeeObjMetadata(
            seats=self.seats + other.seats,
            api_calls=self.api_calls + other.api_calls,
            projects=self.projects + other.projects,
        )

    def __mul__(self, other):
        if not isinstance(other, int):
            raise TypeError("Unable to multiply by anything other than an integer.")

        return ChargebeeObjMetadata(
            **{k: v * other if v else v for k, v in self.__dict__.items()}
        )


class ChargebeeItem(Enum):
    PLAN = "Plan"
    ADDON = "Addon"

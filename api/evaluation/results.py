import re

from evaluation.types import FlagResult

__all__ = ("get_split_weight",)

_SPLIT_REASON = re.compile(r"SPLIT; weight=(?P<weight>.+)")


def get_split_weight(flag_result: FlagResult) -> float | None:
    """The weight of the variant `flag_result` was split into, if it was split."""
    if match := _SPLIT_REASON.fullmatch(flag_result["reason"]):
        return float(match["weight"])
    return None

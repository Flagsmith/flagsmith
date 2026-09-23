from evaluation.types import FlagResult

__all__ = ("get_split_weight",)


def get_split_weight(flag_result: FlagResult) -> float | None:
    """The weight of the variant `flag_result` was split into, if it was split."""
    reason = dict(
        part.partition("=")[::2] for part in flag_result["reason"].split("; ")
    )
    if "SPLIT" in reason and "weight" in reason:
        return float(reason["weight"])
    return None

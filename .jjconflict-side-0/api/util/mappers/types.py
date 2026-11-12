from decimal import Decimal
from typing import TypeAlias, Union

DocumentValue: TypeAlias = Union[
    dict[str, "DocumentValue"],
    list["DocumentValue"],
    str,
    bytes,
    bool,
    None,
    Decimal,
]
Document: TypeAlias = dict[str, "DocumentValue"]

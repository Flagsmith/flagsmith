from dataclasses import dataclass, field
from typing import Optional, Union

from segment_membership.constants import AtomKind


@dataclass(frozen=True)
class AtomKey:
    """Canonical key identifying an atom within an environment."""

    kind: AtomKind
    property: str
    operator: str
    operand_canonical: Optional[str]
    segment_key: Optional[str]


@dataclass(frozen=True)
class AtomNode:
    key: AtomKey
    negated: bool = False


@dataclass
class AndNode:
    children: list["PredicateTree"] = field(default_factory=list)


@dataclass
class OrNode:
    children: list["PredicateTree"] = field(default_factory=list)


@dataclass
class TrueNode:
    """Universe — all ordinals in the env. Lets nested rules with empty
    conditions short-circuit cleanly."""


@dataclass
class FalseNode:
    """Empty set — never a member."""


PredicateTree = Union[AtomNode, AndNode, OrNode, TrueNode, FalseNode]

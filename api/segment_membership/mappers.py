"""Map ORM Segment objects to atom catalogues and predicate trees.

A segment evaluates as `is_context_in_segment` in the flag engine:
  - Top-level rules are AND-combined.
  - Each rule is `conditions_matcher(type)(conditions) AND all(nested_rules)`.
  - `type=ALL` → AND of conditions; `ANY` → OR; `NONE` → AND of negated conditions.

We translate this to a `PredicateTree` whose leaves are `AtomNode`s, and we
collect the set of unique atom keys referenced by the segment.
"""

from typing import Iterable, cast

from flag_engine.context.types import StrValueSegmentCondition
from flag_engine.segments import constants as engine_constants

from segment_membership.constants import (
    KIND_ENVIRONMENT_NAME,
    KIND_IDENTIFIER,
    KIND_IDENTITY_KEY,
    KIND_TRAIT,
    PROPERTY_ENVIRONMENT_NAME,
    PROPERTY_IDENTITY_IDENTIFIER,
    PROPERTY_IDENTITY_KEY,
    AtomKind,
)
from segment_membership.dataclasses import (
    AndNode,
    AtomKey,
    AtomNode,
    FalseNode,
    OrNode,
    PredicateTree,
    TrueNode,
)
from segment_membership.models import Atom
from segments.models import Condition, Segment, SegmentRule


def map_segment_condition_to_atom_kind(condition: Condition) -> AtomKind:
    """Return the atom kind for a segment condition based on its property
    and operator."""
    property_value = condition.property
    if not property_value:
        # The only legitimate empty-property case is legacy PERCENTAGE_SPLIT,
        # which the engine evaluates against identity.key.
        if condition.operator == engine_constants.PERCENTAGE_SPLIT:
            return KIND_IDENTITY_KEY
        # Empty property with any other operator is a malformed condition;
        # treat it as a trait atom with an empty key so the engine returns
        # False for everyone (mirrors current production behaviour).
        return KIND_TRAIT
    if property_value == PROPERTY_IDENTITY_IDENTIFIER:
        return KIND_IDENTIFIER
    if property_value == PROPERTY_IDENTITY_KEY:
        return KIND_IDENTITY_KEY
    if property_value == PROPERTY_ENVIRONMENT_NAME:
        return KIND_ENVIRONMENT_NAME
    return KIND_TRAIT


def map_segment_condition_to_operand_canonical(
    condition: Condition,
) -> str | None:
    """Return a canonical string form of a condition's operand so equivalent
    declarations collapse to the same atom. PoC: trim whitespace, leave the
    rest alone."""
    if condition.value is None:
        return None
    return condition.value.strip()


def map_atom_to_engine_condition(atom: Atom) -> StrValueSegmentCondition:
    """Project an Atom row into the flag-engine's `SegmentCondition` shape so
    it can be evaluated by `context_matches_condition`."""
    return cast(
        StrValueSegmentCondition,
        {
            "property": atom.property,
            "operator": atom.operator,
            "value": atom.operand_canonical or "",
        },
    )


def map_segment_condition_to_atom_key(
    condition: Condition,
    segment: Segment,
) -> AtomKey:
    salted = condition.operator == engine_constants.PERCENTAGE_SPLIT
    return AtomKey(
        kind=map_segment_condition_to_atom_kind(condition),
        property=condition.property or "",
        operator=condition.operator,
        operand_canonical=map_segment_condition_to_operand_canonical(condition),
        segment_key=str(segment.pk) if salted else None,
    )


def _map_conditions_to_predicate_tree(
    conditions: Iterable[Condition],
    rule_type: str,
    segment: Segment,
) -> PredicateTree:
    cond_list = list(conditions)
    if not cond_list:
        return TrueNode()
    nodes: list[PredicateTree] = [
        AtomNode(key=map_segment_condition_to_atom_key(c, segment)) for c in cond_list
    ]
    if rule_type == SegmentRule.ALL_RULE:
        return AndNode(children=nodes)
    if rule_type == SegmentRule.ANY_RULE:
        return OrNode(children=nodes)
    if rule_type == SegmentRule.NONE_RULE:
        # NONE = none of the conditions match = AND of negations.
        return AndNode(
            children=[
                AtomNode(key=n.key, negated=True)  # type: ignore[union-attr]
                for n in nodes
            ]
        )
    # Defensive — unknown rule type collapses to False.
    return FalseNode()


def _map_segment_rule_to_predicate_tree(
    rule: SegmentRule,
    segment: Segment,
) -> PredicateTree:
    cond_tree = _map_conditions_to_predicate_tree(
        conditions=rule.conditions.all(),
        rule_type=rule.type,
        segment=segment,
    )
    nested = [
        _map_segment_rule_to_predicate_tree(child, segment)
        for child in rule.rules.all()
    ]
    if not nested:
        return cond_tree
    return AndNode(children=[cond_tree, *nested])


def map_segment_to_predicate_tree(segment: Segment) -> PredicateTree:
    """Map a Segment to a PredicateTree. Top-level rules are AND-combined."""
    rule_trees = [
        _map_segment_rule_to_predicate_tree(r, segment) for r in segment.rules.all()
    ]
    if not rule_trees:
        return FalseNode()
    return AndNode(children=rule_trees)


def map_predicate_tree_to_atom_keys(tree: PredicateTree) -> set[AtomKey]:
    """Walk the tree and return the set of unique atom keys."""
    keys: set[AtomKey] = set()
    _collect_atom_keys(tree, keys)
    return keys


def _collect_atom_keys(tree: PredicateTree, keys: set[AtomKey]) -> None:
    if isinstance(tree, AtomNode):
        keys.add(tree.key)
    elif isinstance(tree, (AndNode, OrNode)):
        for child in tree.children:
            _collect_atom_keys(child, keys)

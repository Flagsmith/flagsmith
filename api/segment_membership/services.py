"""Services for the segment membership index.

The model is a finite atom basis materialised as Roaring bitmaps; segment
membership is composed via Boolean algebra over those bitmaps. See the RFC
in `segment-membership-rfc.md`.

Ordinals: this module uses `Identity.id` directly as the Roaring bitmap ord
for an env's atoms. No separate ordinal-mapping table — atoms are still
env-scoped, but a bitmap's ords are just the global Postgres primary keys
of the identities that satisfy the predicate in that env. Trade-offs are
captured in the RFC's "Ordinal allocation" section.
"""

import random
from collections.abc import Iterable
from typing import Any

import structlog
from flag_engine.context.types import EvaluationContext
from flag_engine.segments.evaluator import context_matches_condition
from pyroaring import BitMap

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from segment_membership.constants import KIND_IDENTIFIER, KIND_IDENTITY_KEY
from segment_membership.dataclasses import (
    AndNode,
    AtomKey,
    AtomNode,
    FalseNode,
    OrNode,
    PredicateTree,
    TrueNode,
)
from segment_membership.mappers import (
    map_atom_to_engine_condition,
    map_predicate_tree_to_atom_keys,
    map_segment_to_predicate_tree,
)
from segment_membership.models import Atom, AtomBitmap
from segments.models import Segment
from util.mappers.engine import map_environment_to_evaluation_context

logger = structlog.get_logger("segment_membership")


# --- atom catalogue ----------------------------------------------------------


def ensure_atoms(
    environment: Environment,
    segment: Segment,
) -> dict[AtomKey, Atom]:
    """Upsert Atom rows for every unique atom key referenced by the segment."""
    tree = map_segment_to_predicate_tree(segment)
    keys = map_predicate_tree_to_atom_keys(tree)
    return _upsert_atoms(environment, keys)


def _upsert_atoms(
    environment: Environment,
    keys: Iterable[AtomKey],
) -> dict[AtomKey, Atom]:
    out: dict[AtomKey, Atom] = {}
    for key in keys:
        atom, _ = Atom.objects.get_or_create(
            environment=environment,
            kind=key.kind,
            property=key.property,
            operator=key.operator,
            operand_canonical=key.operand_canonical,
            segment_key=key.segment_key,
        )
        out[key] = atom
    return out


# --- engine bridge -----------------------------------------------------------


def evaluate_atom(
    atom: Atom,
    context: EvaluationContext[Any, Any],
) -> bool:
    """Evaluate one atom against a pre-built engine context."""
    return context_matches_condition(
        context=context,
        condition=map_atom_to_engine_condition(atom),
        segment_key=atom.segment_key or "",
    )


# --- bitmap storage ----------------------------------------------------------


def load_bitmap(atom: Atom) -> BitMap:
    try:
        blob = atom.bitmap.blob
    except AtomBitmap.DoesNotExist:
        return BitMap()
    return BitMap.deserialize(bytes(blob)) if blob else BitMap()


def save_bitmap(atom: Atom, bitmap: BitMap) -> None:
    blob = bitmap.serialize()
    AtomBitmap.objects.update_or_create(
        atom=atom,
        defaults={"blob": blob, "cardinality": len(bitmap)},
    )


def universe_bitmap(environment: Environment) -> BitMap:
    """All identity PKs in this environment — the universe used for negation."""
    ids = Identity.objects.filter(environment=environment).values_list("id", flat=True)
    return BitMap(ids)


# --- predicate tree → bitmap -------------------------------------------------


class _UniverseCache:
    """Lazy accessor for the env's universe bitmap.

    The universe is `Identity.id` for every identity in the env — only
    consulted when a NONE rule (negation) or an empty AND/TrueNode is
    encountered. Most segments never need it, so we defer the read.
    """

    def __init__(self, environment: Environment):
        self._environment = environment
        self._bm: BitMap | None = None

    def get(self) -> BitMap:
        if self._bm is None:
            self._bm = universe_bitmap(self._environment)
        return self._bm


def _compose(
    tree: PredicateTree,
    atoms_by_key: dict[AtomKey, Atom],
    universe: _UniverseCache,
) -> BitMap:
    if isinstance(tree, TrueNode):
        return BitMap(universe.get())
    if isinstance(tree, FalseNode):
        return BitMap()
    if isinstance(tree, AtomNode):
        atom = atoms_by_key.get(tree.key)
        bm = load_bitmap(atom) if atom is not None else BitMap()
        if tree.negated:
            return BitMap(universe.get()) - bm
        return bm
    if isinstance(tree, AndNode):
        if not tree.children:
            return BitMap(universe.get())
        children = [_compose(c, atoms_by_key, universe) for c in tree.children]
        # Smallest-first to minimise intermediate work.
        children.sort(key=len)
        result = children[0]
        for c in children[1:]:
            result = result & c
        return result
    if isinstance(tree, OrNode):
        union: BitMap = BitMap()
        for child in tree.children:
            union = union | _compose(child, atoms_by_key, universe)
        return union
    raise ValueError(f"unknown predicate tree node: {tree!r}")


def compute_membership_bitmap(
    segment: Segment,
    environment: Environment,
) -> BitMap:
    tree = map_segment_to_predicate_tree(segment)
    keys = map_predicate_tree_to_atom_keys(tree)
    atoms_by_key = _load_atoms(environment, keys)
    return _compose(tree, atoms_by_key, _UniverseCache(environment))


def _load_atoms(
    environment: Environment,
    keys: Iterable[AtomKey],
) -> dict[AtomKey, Atom]:
    out: dict[AtomKey, Atom] = {}
    for key in keys:
        try:
            atom = Atom.objects.get(
                environment=environment,
                kind=key.kind,
                property=key.property,
                operator=key.operator,
                operand_canonical=key.operand_canonical,
                segment_key=key.segment_key,
            )
        except Atom.DoesNotExist:
            continue
        out[key] = atom
    return out


# --- read API ----------------------------------------------------------------


def count(segment: Segment, environment: Environment) -> int:
    return len(compute_membership_bitmap(segment, environment))


def iter_members(
    segment: Segment,
    environment: Environment,
    cursor: int = 0,
    limit: int = 100,
) -> list[Identity]:
    bitmap = compute_membership_bitmap(segment, environment)
    ids: list[int] = []
    for ident_id in bitmap:
        if ident_id < cursor:
            continue
        ids.append(ident_id)
        if len(ids) >= limit:
            break
    return _ids_to_identities(ids)


def sample(
    segment: Segment,
    environment: Environment,
    n: int,
) -> list[Identity]:
    bitmap = compute_membership_bitmap(segment, environment)
    cardinality = len(bitmap)
    if cardinality <= n:
        ids = list(bitmap)
    else:
        # Roaring supports rank-select in O(log N), so we pick n random ranks
        # and resolve them directly. Avoids iterating the whole bitmap.
        indices = random.sample(range(cardinality), n)
        ids = [bitmap[i] for i in indices]
    return _ids_to_identities(ids)


def _ids_to_identities(ids: list[int]) -> list[Identity]:
    if not ids:
        return []
    rows = Identity.objects.filter(id__in=ids)
    by_id = {ident.id: ident for ident in rows}
    return [by_id[i] for i in ids if i in by_id]


# --- backfill ----------------------------------------------------------------


def backfill_segment(
    environment: Environment,
    segment: Segment,
    *,
    rebuild: bool = False,
) -> dict[int, int]:
    """Ensure atoms exist and backfill any missing bitmaps for `segment` in
    `environment`. Returns `{atom_id: cardinality}`.

    With `rebuild=True`, every atom's bitmap is recomputed even if present.
    """
    atoms_by_key = ensure_atoms(environment, segment)
    atoms = list(atoms_by_key.values())
    return backfill_atoms(environment, atoms, rebuild=rebuild)


def backfill_segments(
    environment: Environment,
    segments: Iterable[Segment],
    *,
    rebuild: bool = False,
) -> dict[int, int]:
    """Ensure atoms across multiple segments and backfill them in one identity
    pass. Each identity is loaded and evaluated against the union of atoms,
    so backfill is `O(|I_env| · |atoms|)` rather than `O(|I_env| · |segments|)`.
    """
    atoms_by_key: dict[AtomKey, Atom] = {}
    for segment in segments:
        atoms_by_key.update(ensure_atoms(environment, segment))
    return backfill_atoms(environment, list(atoms_by_key.values()), rebuild=rebuild)


def backfill_atoms(
    environment: Environment,
    atoms: list[Atom],
    *,
    rebuild: bool = False,
) -> dict[int, int]:
    if not atoms:
        return {}

    if not rebuild:
        existing = set(
            AtomBitmap.objects.filter(atom__in=atoms).values_list("atom_id", flat=True)
        )
        atoms = [a for a in atoms if a.id not in existing]
        if not atoms:
            return {}

    logger.info(
        "backfill.atoms.start",
        environment__id=environment.id,
        atoms__count=len(atoms),
    )

    bitmaps: dict[int, BitMap] = {atom.id: BitMap() for atom in atoms}

    queryset = (
        Identity.objects.filter(environment=environment)
        .only("id", "identifier", "environment_id")
        .prefetch_related("identity_traits")
    )

    processed = 0
    for identity in queryset.iterator(chunk_size=2_000):
        traits = list(identity.identity_traits.all())
        ctx = map_environment_to_evaluation_context(
            environment=environment,
            identity=identity,
            traits=traits,
        )
        for atom in atoms:
            try:
                if evaluate_atom(atom, ctx):
                    bitmaps[atom.id].add(identity.id)
            except Exception:
                logger.exception(
                    "backfill.atom.eval_failed",
                    environment__id=environment.id,
                    atom__id=atom.id,
                    identity__id=identity.id,
                )
        processed += 1

    cardinalities: dict[int, int] = {}
    for atom in atoms:
        bm = bitmaps[atom.id]
        save_bitmap(atom, bm)
        cardinalities[atom.id] = len(bm)

    logger.info(
        "backfill.atoms.completed",
        environment__id=environment.id,
        atoms__count=len(atoms),
        identities__count=processed,
    )
    return cardinalities


# --- maintenance hooks -------------------------------------------------------


def on_identity_created(identity: Identity) -> None:
    """Evaluate identifier/identity-key atoms for a newly-created identity.
    With PK-as-ordinal there's nothing to allocate — identity.id is the ord."""
    environment = identity.environment
    atoms = list(
        Atom.objects.filter(
            environment=environment,
            kind__in=[KIND_IDENTIFIER, KIND_IDENTITY_KEY],
        )
    )
    if not atoms:
        return
    ctx = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
        traits=[],
    )
    _apply_atom_bits(atoms, ctx, identity.id)


def on_traits_changed(
    identity: Identity,
    changed_keys: Iterable[str],
) -> None:
    """Re-evaluate every atom whose property is among `changed_keys`."""
    keys = list({k for k in changed_keys if k})
    if not keys:
        return
    environment = identity.environment
    atoms = list(Atom.objects.filter(environment=environment, property__in=keys))
    if not atoms:
        return
    # Bypass any prefetched `identity_traits` cache the caller may carry — we
    # need post-write state, not whatever was loaded earlier in the request.
    traits = list(Trait.objects.filter(identity=identity))
    ctx = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
        traits=traits,
    )
    _apply_atom_bits(atoms, ctx, identity.id)


def on_identity_deleted(identity_id: int, environment_id: int) -> None:
    """Clear the deleted identity's bit in every atom for the env."""
    bitmaps = AtomBitmap.objects.filter(
        atom__environment_id=environment_id
    ).select_related("atom")
    for ab in bitmaps:
        bm = BitMap.deserialize(bytes(ab.blob)) if ab.blob else BitMap()
        if identity_id in bm:
            bm.discard(identity_id)
            ab.blob = bm.serialize()
            ab.cardinality = len(bm)
            ab.save(update_fields=["blob", "cardinality", "updated_at"])


def _apply_atom_bits(
    atoms: list[Atom],
    context: EvaluationContext[Any, Any],
    ord_: int,
) -> None:
    for atom in atoms:
        try:
            matches = evaluate_atom(atom, context)
        except Exception:
            logger.exception("atom.eval_failed", atom__id=atom.id)
            continue
        bm = load_bitmap(atom)
        present = ord_ in bm
        if matches and not present:
            bm.add(ord_)
        elif not matches and present:
            bm.discard(ord_)
        else:
            continue
        save_bitmap(atom, bm)

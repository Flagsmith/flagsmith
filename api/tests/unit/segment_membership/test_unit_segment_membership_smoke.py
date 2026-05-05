"""End-to-end smoke / differential test for the segment membership PoC.

Builds a synthetic environment with a mix of operators, runs
`services.backfill_segment`, then verifies that the bitmap-derived membership
matches the live flag engine for every identity.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, cast

import pytest
from flag_engine.segments import constants as op
from flag_engine.segments.evaluator import is_context_in_segment

from core.constants import INTEGER, STRING
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from environments.sdk.types import SDKTraitData
from segment_membership import services
from segment_membership.constants import (
    PROPERTY_IDENTITY_IDENTIFIER,
)
from segment_membership.models import Atom, AtomBitmap
from segments.models import Condition, Segment, SegmentRule
from util.mappers.engine import (
    map_environment_to_evaluation_context,
    map_segment_to_segment_context,
)


@pytest.fixture
def segment_membership_enabled(settings: Any) -> None:
    """Enable the segment membership maintenance signals for a test."""
    settings.SEGMENT_MEMBERSHIP_ENABLED = True


@pytest.fixture
def populated_environment(environment: Environment) -> Environment:
    """Seed 30 identities with diverse traits."""
    countries = ["US", "GB", "DE", "FR", "ES"]
    plans = ["free", "pro", "enterprise"]
    for i in range(30):
        identity = Identity.objects.create(
            identifier=f"user-{i:03d}",
            environment=environment,
        )
        Trait.objects.create(
            identity=identity,
            trait_key="country",
            value_type=STRING,
            string_value=countries[i % len(countries)],
        )
        Trait.objects.create(
            identity=identity,
            trait_key="plan",
            value_type=STRING,
            string_value=plans[i % len(plans)],
        )
        Trait.objects.create(
            identity=identity,
            trait_key="age",
            value_type=INTEGER,
            integer_value=18 + i,
        )
        if i % 4 == 0:
            Trait.objects.create(
                identity=identity,
                trait_key="email",
                value_type=STRING,
                string_value=f"u{i}@example.com",
            )
    return environment


def _make_segment(
    project_id: int,
    name: str,
    conditions: list[tuple[str | None, str, str]],
) -> Segment:
    segment: Segment = Segment.objects.create(name=name, project_id=project_id)
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    for prop, oper, value in conditions:
        Condition.objects.create(
            rule=rule,
            property=prop,
            operator=oper,
            value=value,
        )
    return segment


@pytest.fixture
def segments_under_test(populated_environment: Environment) -> list[Segment]:
    project_id = populated_environment.project_id
    return [
        _make_segment(
            project_id,
            "country=US",
            [("country", op.EQUAL, "US")],
        ),
        _make_segment(
            project_id,
            "plan in pro,enterprise",
            [("plan", op.IN, "pro,enterprise")],
        ),
        _make_segment(
            project_id,
            "age >= 30",
            [("age", op.GREATER_THAN_INCLUSIVE, "30")],
        ),
        _make_segment(
            project_id,
            "email regex",
            [("email", op.REGEX, r"^u\d+@example\.com$")],
        ),
        _make_segment(
            project_id,
            "email is set",
            [("email", op.IS_SET, "")],
        ),
        _make_segment(
            project_id,
            "country US AND plan pro",
            [("country", op.EQUAL, "US"), ("plan", op.EQUAL, "pro")],
        ),
        _make_segment(
            project_id,
            "identifier % split 50",
            [(PROPERTY_IDENTITY_IDENTIFIER, op.PERCENTAGE_SPLIT, "50")],
        ),
        _make_segment(
            project_id,
            "age modulo 5|0",
            [("age", op.MODULO, "5|0")],
        ),
    ]


def _engine_match(
    environment: Environment,
    segment: Segment,
    identity: Identity,
) -> bool:
    traits = list(identity.identity_traits.all())
    ctx = map_environment_to_evaluation_context(
        environment=environment,
        identity=identity,
        traits=traits,
    )
    return is_context_in_segment(ctx, map_segment_to_segment_context(segment))


def _index_match(bitmap: object, identity: Identity) -> bool:
    return identity.id in bitmap  # type: ignore[operator]


def _iter_identities(environment: Environment) -> Iterator[Identity]:
    yield from Identity.objects.filter(environment=environment).prefetch_related(
        "identity_traits"
    )


def test_backfill__diverse_operator_segments__bitmap_matches_engine_for_every_identity(
    populated_environment: Environment,
    segments_under_test: list[Segment],
) -> None:
    # Given a populated environment and a battery of segments covering the operator vocabulary
    environment = populated_environment

    # When we backfill the index for each segment
    for segment in segments_under_test:
        services.backfill_segment(environment, segment)

    # Then every (segment, identity) pair agrees with the engine
    mismatches: list[tuple[str, str, bool, bool]] = []
    for segment in segments_under_test:
        bitmap = services.compute_membership_bitmap(segment, environment)
        for identity in _iter_identities(environment):
            engine = _engine_match(environment, segment, identity)
            indexed = _index_match(bitmap, identity)
            if engine != indexed:
                mismatches.append((segment.name, identity.identifier, engine, indexed))

    assert mismatches == [], f"Differential mismatches: {mismatches[:10]}"


def test_count_and_iter_members__country_us__matches_engine_membership_set(
    populated_environment: Environment,
    segments_under_test: list[Segment],
) -> None:
    # Given the country=US segment from the battery
    environment = populated_environment
    segment = next(s for s in segments_under_test if s.name == "country=US")
    services.backfill_segment(environment, segment)

    # When we ask the index for count and members
    count = services.count(segment, environment)
    members = services.iter_members(segment, environment, cursor=0, limit=1000)

    # Then they agree with the engine
    expected_identifiers = {
        identity.identifier
        for identity in _iter_identities(environment)
        if _engine_match(environment, segment, identity)
    }
    assert count == len(expected_identifiers)
    assert {m.identifier for m in members} == expected_identifiers


def test_atom_catalogue__country_us_segment__creates_one_trait_atom(
    populated_environment: Environment,
    segments_under_test: list[Segment],
) -> None:
    # Given the country=US segment
    environment = populated_environment
    segment = next(s for s in segments_under_test if s.name == "country=US")

    # When we ensure atoms
    services.ensure_atoms(environment, segment)

    # Then exactly one trait atom is registered
    atoms = list(Atom.objects.filter(environment=environment))
    assert len(atoms) == 1
    atom = atoms[0]
    assert atom.kind == "trait"
    assert atom.property == "country"
    assert atom.operator == op.EQUAL
    assert atom.operand_canonical == "US"
    assert atom.segment_key is None


def test_atom_catalogue__percentage_split__atom_carries_segment_key(
    populated_environment: Environment,
    segments_under_test: list[Segment],
) -> None:
    # Given the % Split segment
    environment = populated_environment
    segment = next(s for s in segments_under_test if "% split" in s.name)

    # When we ensure atoms
    services.ensure_atoms(environment, segment)

    # Then the atom is salted by segment id
    atom = Atom.objects.get(environment=environment, operator=op.PERCENTAGE_SPLIT)
    assert atom.segment_key == str(segment.pk)


def test_ordinals__pk_used_directly__bitmap_contains_identity_pks(
    populated_environment: Environment,
    segments_under_test: list[Segment],
) -> None:
    # Given the country=US segment
    environment = populated_environment
    segment = next(s for s in segments_under_test if s.name == "country=US")

    # When we backfill
    services.backfill_segment(environment, segment)

    # Then the bitmap contains exactly the matching identities' primary keys
    atom = Atom.objects.get(environment=environment, property="country")
    bitmap = services.load_bitmap(atom)
    expected_ids = set(
        Identity.objects.filter(
            environment=environment, identity_traits__string_value="US"
        ).values_list("id", flat=True)
    )
    assert set(bitmap) == expected_ids


def test_update_traits__bulk_write_with_index_enabled__bitmap_reflects_new_value(
    populated_environment: Environment,
    segment_membership_enabled: None,
) -> None:
    # Given a country=US segment with a backfilled bitmap
    environment = populated_environment
    segment = _make_segment(
        environment.project_id,
        "country=US",
        [("country", op.EQUAL, "US")],
    )
    services.backfill_segment(environment, segment)
    atom = Atom.objects.get(environment=environment, property="country")

    # And an identity that does not currently match the segment
    non_matching = next(
        identity
        for identity in _iter_identities(environment)
        if not _engine_match(environment, segment, identity)
    )
    initial = AtomBitmap.objects.get(atom=atom).cardinality

    # When the SDK ingestion path bulk-updates the country trait to US
    non_matching.update_traits(
        [cast(SDKTraitData, {"trait_key": "country", "trait_value": "US"})]
    )

    # Then the bitmap reflects the new membership without an explicit backfill
    refreshed = AtomBitmap.objects.get(atom=atom)
    assert refreshed.cardinality == initial + 1
    bitmap = services.compute_membership_bitmap(segment, environment)
    assert non_matching.id in bitmap


def test_update_traits__bulk_delete_with_index_enabled__bitmap_clears_member(
    populated_environment: Environment,
    segment_membership_enabled: None,
) -> None:
    # Given a country=US segment with a backfilled bitmap
    environment = populated_environment
    segment = _make_segment(
        environment.project_id,
        "country=US",
        [("country", op.EQUAL, "US")],
    )
    services.backfill_segment(environment, segment)
    atom = Atom.objects.get(environment=environment, property="country")

    # And an identity that currently matches the segment
    matching = next(
        identity
        for identity in _iter_identities(environment)
        if _engine_match(environment, segment, identity)
    )
    initial = AtomBitmap.objects.get(atom=atom).cardinality

    # When the SDK ingestion path nulls out the country trait
    matching.update_traits(
        [cast(SDKTraitData, {"trait_key": "country", "trait_value": None})]
    )

    # Then the identity is removed from the bitmap
    refreshed = AtomBitmap.objects.get(atom=atom)
    assert refreshed.cardinality == initial - 1
    bitmap = services.compute_membership_bitmap(segment, environment)
    assert matching.id not in bitmap


def test_bitmap_storage__after_backfill__atom_bitmaps_persist_with_correct_cardinality(
    populated_environment: Environment,
    segments_under_test: list[Segment],
) -> None:
    # Given the country=US segment
    environment = populated_environment
    segment = next(s for s in segments_under_test if s.name == "country=US")

    # When we backfill
    services.backfill_segment(environment, segment)

    # Then the bitmap row exists with the expected cardinality
    atom = Atom.objects.get(environment=environment, property="country")
    bitmap = AtomBitmap.objects.get(atom=atom)
    expected = sum(
        1
        for identity in _iter_identities(environment)
        if any(
            t.trait_key == "country" and t.string_value == "US"
            for t in identity.identity_traits.all()
        )
    )
    assert bitmap.cardinality == expected

"""Differentially verify the segment membership index against the live engine.

For each identity (or a random sample), compare:

  * `engine.is_context_in_segment(context, segment_context)` — the source of truth.
  * `identity.ord ∈ B_S`            — the index's answer.

Any mismatch is a PoC failure. Also reports rough timings: backfilled count,
sample evaluation time, bitmap query time.
"""

import random
import time
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from flag_engine.segments.evaluator import is_context_in_segment

from environments.identities.models import Identity
from environments.models import Environment
from segment_membership import services
from segments.models import Segment
from util.mappers.engine import (
    map_environment_to_evaluation_context,
    map_segment_to_segment_context,
)


class Command(BaseCommand):
    help = (
        "Differentially verify the segment membership index against the "
        "live flag engine."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--environment", type=int, required=True)
        parser.add_argument("--segment", type=int, required=True)
        parser.add_argument(
            "--sample",
            type=int,
            default=0,
            help="Number of identities to verify. 0 means every identity.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        environment = self._get_environment(options["environment"])
        segment = self._get_segment(options["segment"])

        bitmap_started = time.perf_counter()
        bitmap = services.compute_membership_bitmap(segment, environment)
        bitmap_elapsed = time.perf_counter() - bitmap_started
        self.stdout.write(
            f"Bitmap composed in {bitmap_elapsed * 1000:.1f}ms ({len(bitmap)} members)."
        )

        identities = self._select_identities(environment, options["sample"])
        if not identities:
            raise CommandError("No identities to verify against.")

        mismatches, engine_elapsed = self._compare(
            environment, segment, identities, bitmap
        )
        total = len(identities)
        self.stdout.write(
            f"Evaluated {total} identities in {engine_elapsed:.2f}s "
            f"({engine_elapsed / total * 1000:.2f}ms / identity)."
        )

        if mismatches:
            self._report_mismatches(mismatches, total)
            raise CommandError("Differential verification failed.")

        self.stdout.write(
            self.style.SUCCESS(
                f"OK: {total} identities, 0 mismatches. Bitmap size {len(bitmap)}."
            )
        )

    def _get_environment(self, env_id: int) -> Environment:
        try:
            env: Environment = Environment.objects.get(id=env_id)
        except Environment.DoesNotExist as exc:
            raise CommandError(f"Environment {env_id} not found") from exc
        return env

    def _get_segment(self, seg_id: int) -> Segment:
        try:
            segment: Segment = Segment.live_objects.get(id=seg_id)
        except Segment.DoesNotExist as exc:
            raise CommandError(f"Segment {seg_id} not found") from exc
        return segment

    def _select_identities(
        self, environment: Environment, sample_n: int
    ) -> list[Identity]:
        identities_qs = Identity.objects.filter(environment=environment)
        if sample_n:
            ids = list(identities_qs.values_list("id", flat=True))
            if len(ids) > sample_n:
                ids = random.sample(ids, sample_n)
            identities_qs = Identity.objects.filter(id__in=ids)
        return list(identities_qs.prefetch_related("identity_traits"))

    def _compare(
        self,
        environment: Environment,
        segment: Segment,
        identities: list[Identity],
        bitmap: Any,
    ) -> tuple[list[tuple[int, str, bool, bool]], float]:
        segment_context = map_segment_to_segment_context(segment)
        mismatches: list[tuple[int, str, bool, bool]] = []
        engine_started = time.perf_counter()
        for identity in identities:
            ctx = map_environment_to_evaluation_context(
                environment=environment,
                identity=identity,
                traits=list(identity.identity_traits.all()),
            )
            engine_match = is_context_in_segment(ctx, segment_context)
            index_match = identity.id in bitmap
            if engine_match != index_match:
                mismatches.append(
                    (identity.id, identity.identifier, engine_match, index_match)
                )
        return mismatches, time.perf_counter() - engine_started

    def _report_mismatches(
        self,
        mismatches: list[tuple[int, str, bool, bool]],
        total: int,
    ) -> None:
        self.stderr.write(
            self.style.ERROR(f"FAILED: {len(mismatches)} mismatches out of {total}.")
        )
        for ident_id, identifier, engine_match, index_match in mismatches[:20]:
            self.stderr.write(
                f"  identity={ident_id} {identifier!r} "
                f"engine={engine_match} index={index_match}"
            )
        if len(mismatches) > 20:
            self.stderr.write(f"  ... and {len(mismatches) - 20} more")

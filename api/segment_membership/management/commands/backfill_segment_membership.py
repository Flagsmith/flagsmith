"""Backfill the segment membership index for a single environment.

Usage::

    ./manage.py backfill_segment_membership --environment <id> --segment <id|all>

The command extracts the atom catalogue from the segment definition(s),
allocates ordinals for any identities missing one, streams identities, and
writes Roaring bitmaps for every atom.
"""

import time
from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from environments.models import Environment
from segment_membership import services
from segments.models import Segment


class Command(BaseCommand):
    help = "Backfill the segment membership index for one or more segments."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--environment",
            type=int,
            required=True,
            help="Environment ID.",
        )
        parser.add_argument(
            "--segment",
            type=str,
            default="all",
            help="Segment ID, or 'all' for every segment in the env's project.",
        )
        parser.add_argument(
            "--rebuild",
            action="store_true",
            help="Rebuild bitmaps even when already present.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        env_id: int = options["environment"]
        segment_arg: str = options["segment"]
        rebuild: bool = options["rebuild"]

        try:
            environment = Environment.objects.get(id=env_id)
        except Environment.DoesNotExist as exc:
            raise CommandError(f"Environment {env_id} not found") from exc

        if segment_arg == "all":
            segments = list(Segment.live_objects.filter(project=environment.project))
        else:
            try:
                segments = [Segment.live_objects.get(id=int(segment_arg))]
            except (Segment.DoesNotExist, ValueError) as exc:
                raise CommandError(f"Segment {segment_arg!r} not found") from exc

        self.stdout.write(
            f"Backfilling {len(segments)} segment(s) in environment {env_id}…"
        )

        total_atoms = 0
        total_set_bits = 0
        started = time.perf_counter()

        for segment in segments:
            seg_started = time.perf_counter()
            cardinalities = services.backfill_segment(
                environment, segment, rebuild=rebuild
            )
            seg_elapsed = time.perf_counter() - seg_started
            atom_count = len(cardinalities)
            set_bits = sum(cardinalities.values())
            total_atoms += atom_count
            total_set_bits += set_bits
            self.stdout.write(
                f"  segment {segment.id} ({segment.name!r}): "
                f"{atom_count} atoms, {set_bits} set bits, {seg_elapsed:.2f}s"
            )

        elapsed = time.perf_counter() - started
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. {len(segments)} segments, {total_atoms} atoms, "
                f"{total_set_bits} set bits, {elapsed:.2f}s total."
            )
        )

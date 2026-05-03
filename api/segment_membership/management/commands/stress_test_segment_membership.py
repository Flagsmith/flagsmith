"""Stress test the segment membership index on synthetic data.

Seeds an isolated organisation/project/environment, bulk-creates N identities
with five traits each, defines a battery of segments covering the operator
vocabulary, then reports:

  * Seeding time.
  * Backfill time and bitmap bytes per atom.
  * Read latency: count, sample(100), page(0..200) — best of 5 runs.
  * Write overhead: `update_traits` p50/p95 with the index disabled vs
    enabled, over 200 calls.

Usage::

    ./manage.py stress_test_segment_membership --identities 100000

Re-run with `--reset` to drop and recreate the test env. Otherwise the
command reuses the previous run's data and skips seeding.
"""

import math
import os
import random
import statistics
import time
from argparse import ArgumentParser
from typing import Any, cast

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from flag_engine.segments import constants as op

from core.constants import FLOAT, INTEGER, STRING
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from environments.sdk.types import SDKTraitData
from organisations.models import Organisation
from projects.models import Project
from segment_membership import services
from segment_membership.constants import PROPERTY_IDENTITY_IDENTIFIER
from segment_membership.models import Atom, AtomBitmap
from segments.models import Condition, Segment, SegmentRule

STRESS_ORG_NAME = "Segment membership stress org"
STRESS_PROJECT_NAME = "Segment membership stress project"
STRESS_ENV_NAME = "stress"

COUNTRIES = ["US", "GB", "DE", "FR", "ES", "JP", "BR", "IN"]
PLANS = ["free", "pro", "enterprise"]


class Command(BaseCommand):
    help = "Stress test the segment membership index on synthetic data."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--identities", type=int, default=10_000)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--reset", action="store_true")
        parser.add_argument(
            "--write-overhead-iterations",
            type=int,
            default=200,
            help="Number of update_traits calls per write-overhead phase.",
        )
        parser.add_argument(
            "--skip-backfill",
            action="store_true",
            help="Reuse existing bitmaps; skip the backfill phase.",
        )
        parser.add_argument(
            "--num-segments",
            type=int,
            default=8,
            help=(
                "Total number of segments to define. With <= 8 the original "
                "hand-curated battery is used; above that, segments are "
                "generated programmatically with diverse operator shapes."
            ),
        )

    def handle(self, *args: Any, **options: Any) -> None:
        n: int = options["identities"]
        rng = random.Random(options["seed"])
        reset: bool = options["reset"]
        write_iters: int = options["write_overhead_iterations"]
        skip_backfill: bool = options["skip_backfill"]
        num_segments: int = options["num_segments"]

        organisation = self._ensure_org()
        project = self._ensure_project(organisation)
        environment = self._ensure_env(project, reset=reset)

        existing_identities = Identity.objects.filter(environment=environment).count()
        if existing_identities and existing_identities != n:
            raise CommandError(
                f"Environment already has {existing_identities} identities, "
                f"expected {n}. Re-run with --reset."
            )
        if existing_identities == 0:
            self._seed(environment, n, rng)
        else:
            self.stdout.write(
                f"Reusing existing {existing_identities} identities (skip --reset to keep)."
            )

        segments = self._ensure_segments(project, num_segments=num_segments, rng=rng)

        self._report_environment(environment)
        if skip_backfill:
            backfill_results = self._collect_existing_backfill_stats(
                environment, segments
            )
        else:
            backfill_results = self._phase_backfill(environment, segments)
        read_results = self._phase_read(environment, segments)
        write_results = self._phase_write_overhead(environment, write_iters, rng)
        bitmap_total = self._bitmap_bytes(environment)

        self._print_summary(
            n=n,
            backfill=backfill_results,
            reads=read_results,
            write_results=write_results,
            bitmap_total_bytes=bitmap_total,
        )

    # ------------------------------------------------------------------ env

    def _ensure_org(self) -> Organisation:
        org: Organisation
        org, _ = Organisation.objects.get_or_create(name=STRESS_ORG_NAME)
        return org

    def _ensure_project(self, organisation: Organisation) -> Project:
        project: Project
        project, _ = Project.objects.get_or_create(
            name=STRESS_PROJECT_NAME,
            organisation=organisation,
        )
        return project

    def _ensure_env(self, project: Project, *, reset: bool) -> Environment:
        existing = Environment.objects.filter(
            project=project, name=STRESS_ENV_NAME
        ).first()
        if existing and reset:
            self.stdout.write("Resetting stress environment…")
            with transaction.atomic():
                AtomBitmap.objects.filter(atom__environment=existing).delete()
                Atom.objects.filter(environment=existing).delete()
                # Segments are project-scoped, so wipe them too.
                Segment.objects.filter(project=project).delete()
                # Cascade deletes traits and identities.
                existing.delete()
            existing = None
        if existing is None:
            existing = Environment.objects.create(project=project, name=STRESS_ENV_NAME)
        return cast(Environment, existing)

    def _ensure_segments(
        self,
        project: Project,
        *,
        num_segments: int,
        rng: random.Random,
    ) -> list[Segment]:
        existing = list(Segment.live_objects.filter(project=project))
        if existing:
            return existing
        if num_segments <= 8:
            return self._curated_segments(project)
        return self._generate_segments(project, n=num_segments, rng=rng)

    def _curated_segments(self, project: Project) -> list[Segment]:
        return [
            self._make_segment(project, "country=US", [("country", op.EQUAL, "US")]),
            self._make_segment(
                project, "plan in pro,enterprise", [("plan", op.IN, "pro,enterprise")]
            ),
            self._make_segment(
                project, "age >= 30", [("age", op.GREATER_THAN_INCLUSIVE, "30")]
            ),
            self._make_segment(project, "email is_set", [("email", op.IS_SET, "")]),
            self._make_segment(
                project, "score modulo 10|0", [("score", op.MODULO, "10|0")]
            ),
            self._make_segment(
                project,
                "country US AND plan pro",
                [("country", op.EQUAL, "US"), ("plan", op.EQUAL, "pro")],
            ),
            self._make_segment(
                project,
                "identifier % split 50",
                [(PROPERTY_IDENTITY_IDENTIFIER, op.PERCENTAGE_SPLIT, "50")],
            ),
            self._make_segment(
                project, "email regex", [("email", op.REGEX, r"^u\d+@example\.com$")]
            ),
        ]

    def _generate_segments(
        self,
        project: Project,
        *,
        n: int,
        rng: random.Random,
    ) -> list[Segment]:
        """Generate `n` segments with a realistic mix of operator shapes.

        The mix is calibrated so that atom dedup mirrors what we expect in
        production: country/plan/age atoms collapse heavily, % Split and
        regex atoms grow ~linearly with segment count (segment-salted or
        unique-operand).
        """
        segments: list[Segment] = []
        countries = COUNTRIES
        plans = PLANS
        for i in range(n):
            bucket = i % 7
            if bucket == 0:
                country = countries[i % len(countries)]
                segments.append(
                    self._make_segment(
                        project,
                        f"country={country} ({i})",
                        [("country", op.EQUAL, country)],
                    )
                )
            elif bucket == 1:
                pair = rng.sample(plans, k=2)
                segments.append(
                    self._make_segment(
                        project,
                        f"plan IN {pair} ({i})",
                        [("plan", op.IN, ",".join(pair))],
                    )
                )
            elif bucket == 2:
                age = 18 + (i % 70)
                segments.append(
                    self._make_segment(
                        project,
                        f"age >= {age} ({i})",
                        [("age", op.GREATER_THAN_INCLUSIVE, str(age))],
                    )
                )
            elif bucket == 3:
                pct = (i * 7) % 99 + 1
                segments.append(
                    self._make_segment(
                        project,
                        f"identifier % split {pct} ({i})",
                        [(PROPERTY_IDENTITY_IDENTIFIER, op.PERCENTAGE_SPLIT, str(pct))],
                    )
                )
            elif bucket == 4:
                # Unique regex per segment.
                pattern = rf"^u{(i * 13) % 1000}\d*@example\.com$"
                segments.append(
                    self._make_segment(
                        project,
                        f"email regex {i}",
                        [("email", op.REGEX, pattern)],
                    )
                )
            elif bucket == 5:
                country = countries[i % len(countries)]
                plan = plans[i % len(plans)]
                segments.append(
                    self._make_segment(
                        project,
                        f"country={country} AND plan={plan} ({i})",
                        [
                            ("country", op.EQUAL, country),
                            ("plan", op.EQUAL, plan),
                        ],
                    )
                )
            else:
                divisor = (i % 7) + 2
                segments.append(
                    self._make_segment(
                        project,
                        f"score % {divisor}=0 ({i})",
                        [("score", op.MODULO, f"{divisor}|0")],
                    )
                )
        return segments

    def _make_segment(
        self,
        project: Project,
        name: str,
        conditions: list[tuple[str | None, str, str]],
    ) -> Segment:
        segment: Segment = Segment.objects.create(name=name, project=project)
        rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        for prop, oper, value in conditions:
            Condition.objects.create(
                rule=rule, property=prop, operator=oper, value=value
            )
        return segment

    # ----------------------------------------------------------------- seed

    def _seed(self, environment: Environment, n: int, rng: random.Random) -> None:
        self.stdout.write(f"Seeding {n} identities + 5 traits each…")
        started = time.perf_counter()
        chunk = 5_000
        for offset in range(0, n, chunk):
            batch_size = min(chunk, n - offset)
            identities = [
                Identity(
                    identifier=f"u{offset + i:08d}",
                    environment=environment,
                )
                for i in range(batch_size)
            ]
            # Postgres populates `id` on the returned objects, no extra SELECT needed.
            created = Identity.objects.bulk_create(identities)
            traits: list[Trait] = []
            for identity in created:
                identity_id = identity.id
                idx = int(identity.identifier[1:])
                traits.append(
                    Trait(
                        identity_id=identity_id,
                        trait_key="country",
                        value_type=STRING,
                        string_value=COUNTRIES[idx % len(COUNTRIES)],
                    )
                )
                traits.append(
                    Trait(
                        identity_id=identity_id,
                        trait_key="plan",
                        value_type=STRING,
                        string_value=PLANS[idx % len(PLANS)],
                    )
                )
                traits.append(
                    Trait(
                        identity_id=identity_id,
                        trait_key="age",
                        value_type=INTEGER,
                        integer_value=18 + (idx % 70),
                    )
                )
                traits.append(
                    Trait(
                        identity_id=identity_id,
                        trait_key="score",
                        value_type=FLOAT,
                        float_value=round(rng.uniform(0, 100), 2),
                    )
                )
                if idx % 4 == 0:
                    traits.append(
                        Trait(
                            identity_id=identity_id,
                            trait_key="email",
                            value_type=STRING,
                            string_value=f"u{idx}@example.com",
                        )
                    )
            Trait.objects.bulk_create(traits, batch_size=2_000)
            self.stdout.write(f"  {min(offset + batch_size, n)}/{n} identities seeded")
        elapsed = time.perf_counter() - started
        self.stdout.write(
            self.style.SUCCESS(f"Seeded in {elapsed:.1f}s ({n / elapsed:,.0f} ids/s).")
        )

    # ----------------------------------------------------------- diagnostics

    def _report_environment(self, environment: Environment) -> None:
        identities = Identity.objects.filter(environment=environment).count()
        traits = Trait.objects.filter(identity__environment=environment).count()
        segments = Segment.live_objects.filter(project=environment.project).count()
        atoms = Atom.objects.filter(environment=environment).count()
        self.stdout.write(
            f"Environment {environment.id}: {identities} identities, "
            f"{traits} traits, {segments} segments, {atoms} atoms."
        )

    # ----------------------------------------------------------- phases

    def _phase_backfill(
        self,
        environment: Environment,
        segments: list[Segment],
    ) -> dict[str, dict[str, float | int]]:
        # Reset bitmaps so we always measure full backfill cost.
        AtomBitmap.objects.filter(atom__environment=environment).delete()

        # Single-pass backfill across all segments.
        started = time.perf_counter()
        cardinalities = services.backfill_segments(environment, segments, rebuild=True)
        elapsed_total = time.perf_counter() - started
        self.stdout.write(
            f"  backfill[ALL {len(segments)} segments, single pass]: "
            f"{elapsed_total:.2f}s, {len(cardinalities)} atoms, "
            f"{sum(cardinalities.values())} set bits"
        )

        results: dict[str, dict[str, float | int]] = {
            "__single_pass__": {
                "elapsed_s": elapsed_total,
                "atoms": len(cardinalities),
                "set_bits": sum(cardinalities.values()),
            }
        }
        for segment in segments:
            seg_card = services.count(segment, environment)
            results[segment.name] = {
                "elapsed_s": elapsed_total / max(len(segments), 1),
                "atoms": 0,
                "set_bits": seg_card,
            }
            self.stdout.write(f"    {segment.name!r}: members={seg_card:,}")
        return results

    def _collect_existing_backfill_stats(
        self,
        environment: Environment,
        segments: list[Segment],
    ) -> dict[str, dict[str, float | int]]:
        """Skip the backfill phase but still report per-segment cardinalities."""
        results: dict[str, dict[str, float | int]] = {
            "__single_pass__": {
                "elapsed_s": 0.0,
                "atoms": Atom.objects.filter(environment=environment).count(),
                "set_bits": 0,
            }
        }
        for segment in segments:
            seg_card = services.count(segment, environment)
            results[segment.name] = {
                "elapsed_s": 0.0,
                "atoms": 0,
                "set_bits": seg_card,
            }
        return results

    def _phase_read(
        self,
        environment: Environment,
        segments: list[Segment],
    ) -> dict[str, dict[str, float]]:
        results: dict[str, dict[str, float]] = {}
        verbose = len(segments) <= 16
        for segment in segments:
            count_ms = self._best_of(lambda: services.count(segment, environment), 5)
            sample_ms = self._best_of(
                lambda: services.sample(segment, environment, 100), 5
            )
            page_ms = self._best_of(
                lambda: services.iter_members(
                    segment, environment, cursor=0, limit=200
                ),
                5,
            )
            results[segment.name] = {
                "count_ms": count_ms,
                "sample100_ms": sample_ms,
                "page200_ms": page_ms,
            }
            if verbose:
                self.stdout.write(
                    f"  read[{segment.name!r}]: count={count_ms:.1f}ms, "
                    f"sample100={sample_ms:.1f}ms, page200={page_ms:.1f}ms"
                )
        return results

    def _phase_write_overhead(
        self,
        environment: Environment,
        iterations: int,
        rng: random.Random,
    ) -> dict[str, dict[str, float]]:
        from task_processor.models import Task
        from task_processor.task_registry import get_task
        from task_processor.task_run_method import TaskRunMethod

        identity_ids = list(
            Identity.objects.filter(environment=environment).values_list(
                "id", flat=True
            )
        )
        sample_ids = rng.sample(identity_ids, k=min(iterations, len(identity_ids)))
        # Halve the workload across phases so each phase touches a disjoint
        # slice. Avoids cross-phase interference (e.g. threads from a prior
        # phase still running while the next phase times its calls).
        phase_size = max(1, len(sample_ids) // 4)
        phase_slices = [
            sample_ids[i * phase_size : (i + 1) * phase_size] for i in range(4)
        ]

        prev_run_method = settings.TASK_RUN_METHOD
        prev_enabled = getattr(settings, "SEGMENT_MEMBERSHIP_ENABLED", False)

        results: dict[str, dict[str, float]] = {}

        try:
            # Phase A: index disabled (signal handlers early-return). Baseline
            # cost of update_traits with no segment-membership work.
            settings.SEGMENT_MEMBERSHIP_ENABLED = False
            Task.objects.all().delete()
            results["disabled"] = self._summarise(
                self._time_update_traits(phase_slices[0], rng)
            )

            # Phase B–D: index enabled, vary TASK_RUN_METHOD.
            settings.SEGMENT_MEMBERSHIP_ENABLED = True

            settings.TASK_RUN_METHOD = TaskRunMethod.SYNCHRONOUSLY
            Task.objects.all().delete()
            results["sync"] = self._summarise(
                self._time_update_traits(phase_slices[1], rng)
            )

            settings.TASK_RUN_METHOD = TaskRunMethod.SEPARATE_THREAD
            Task.objects.all().delete()
            results["thread"] = self._summarise(
                self._time_update_traits(phase_slices[2], rng)
            )
            # Let detached threads finish before measuring next phase.
            time.sleep(2.0)

            # Phase D: TASK_PROCESSOR mode — caller cost is one DB INSERT per
            # delay() call. Then drain the queue and measure throughput.
            Task.objects.all().delete()
            settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR
            timings_processor = self._time_update_traits(phase_slices[3], rng)
            results["processor_enqueue"] = self._summarise(timings_processor)

            queued = Task.objects.filter(completed=False).count()
            # We can't use task_processor.processor.run_tasks here because its
            # metrics objects are only registered when TASK_PROCESSOR_MODE was
            # truthy at import time. Drain by invoking the registered handlers
            # directly — same effect, no metrics dependency.
            drain_started = time.perf_counter()
            drained = 0
            queued_tasks = Task.objects.filter(completed=False).order_by(
                "scheduled_for"
            )
            for task_row in queued_tasks.iterator(chunk_size=500):
                registered = get_task(task_row.task_identifier)
                registered.task_function(*task_row.args, **task_row.kwargs)
                drained += 1
            Task.objects.filter(completed=False).update(completed=True)
            drain_elapsed = time.perf_counter() - drain_started
            results["processor_drain"] = {
                "queued": float(queued),
                "drained": float(drained),
                "elapsed_s": drain_elapsed,
                "per_task_ms": (
                    (drain_elapsed / drained) * 1000 if drained else float("nan")
                ),
            }
        finally:
            settings.TASK_RUN_METHOD = prev_run_method
            settings.SEGMENT_MEMBERSHIP_ENABLED = prev_enabled

        return results

    def _time_update_traits(
        self,
        identity_ids: list[int],
        rng: random.Random,
    ) -> list[float]:
        timings_ms: list[float] = []
        # Salt by current process PID + monotonic nanos so values never
        # collide with prior runs — otherwise update_traits short-circuits
        # the "value unchanged" branch and the maintenance signal silently
        # never fires.
        run_salt = f"{os.getpid()}-{time.time_ns()}"
        for i, ident_id in enumerate(identity_ids):
            new_country = f"COUNTRY_{run_salt}_{rng.randint(0, 1_000_000_000)}_{i}"
            identity = Identity.objects.get(id=ident_id)
            started = time.perf_counter()
            identity.update_traits(
                [
                    cast(
                        SDKTraitData,
                        {"trait_key": "country", "trait_value": new_country},
                    )
                ]
            )
            timings_ms.append((time.perf_counter() - started) * 1000)
        return timings_ms

    # ------------------------------------------------------------- helpers

    def _best_of(self, fn: Any, repeats: int) -> float:
        timings: list[float] = []
        for _ in range(repeats):
            started = time.perf_counter()
            fn()
            timings.append((time.perf_counter() - started) * 1000)
        return min(timings)

    def _summarise(self, timings_ms: list[float]) -> dict[str, float]:
        if not timings_ms:
            return {"p50": math.nan, "p95": math.nan, "mean": math.nan}
        sorted_t = sorted(timings_ms)
        return {
            "p50": statistics.median(sorted_t),
            "p95": sorted_t[max(0, int(len(sorted_t) * 0.95) - 1)],
            "mean": statistics.fmean(sorted_t),
        }

    def _bitmap_bytes(self, environment: Environment) -> int:
        rows = (
            AtomBitmap.objects.filter(atom__environment=environment)
            .extra(select={"size": "octet_length(blob)"})
            .values_list("size", flat=True)
        )
        return sum(rows)

    # -------------------------------------------------------------- output

    def _print_summary(
        self,
        *,
        n: int,
        backfill: dict[str, dict[str, float | int]],
        reads: dict[str, dict[str, float]],
        write_results: dict[str, dict[str, float]],
        bitmap_total_bytes: int,
    ) -> None:
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== STRESS TEST SUMMARY ==="))
        self.stdout.write(f"Identities: {n:,}")
        self.stdout.write(f"Bitmap bytes total: {bitmap_total_bytes:,}")
        self.stdout.write("")
        self._print_backfill_summary(backfill)
        self.stdout.write("")
        self._print_read_summary(reads)
        self.stdout.write("")
        self._print_write_summary(write_results)
        drain = write_results.get("processor_drain")
        if drain is not None:
            self.stdout.write("")
            self.stdout.write("Task processor backlog drain:")
            self.stdout.write(
                f"  enqueued={int(drain['queued'])}, drained={int(drain['drained'])}, "
                f"elapsed={drain['elapsed_s']:.2f}s, "
                f"per-task={drain['per_task_ms']:.2f}ms"
            )

    def _print_backfill_summary(
        self, backfill: dict[str, dict[str, float | int]]
    ) -> None:
        single = backfill.pop("__single_pass__", None)
        if single is not None:
            self.stdout.write(
                f"Backfill (single pass over identities, all segments): "
                f"{single['elapsed_s']:.2f}s, "
                f"{single['atoms']} atoms, "
                f"{single['set_bits']:,} set bits"
            )
        self.stdout.write("Per-segment membership counts:")
        self.stdout.write(f"  {'segment':<32} {'members':>10}")
        for name, row in backfill.items():
            self.stdout.write(f"  {name:<32} {row['set_bits']:>10,}")

    def _print_read_summary(self, reads: dict[str, dict[str, float]]) -> None:
        self.stdout.write("Read latency (best of 5, ms):")
        if len(reads) <= 16:
            self._print_read_per_segment(reads)
        else:
            self._print_read_aggregated(reads)

    def _print_read_per_segment(self, reads: dict[str, dict[str, float]]) -> None:
        self.stdout.write(
            f"  {'segment':<32} {'count':>8} {'sample100':>10} {'page200':>10}"
        )
        for name, row in reads.items():
            self.stdout.write(
                f"  {name:<48} {row['count_ms']:>8.1f} "
                f"{row['sample100_ms']:>10.1f} {row['page200_ms']:>10.1f}"
            )

    def _print_read_aggregated(self, reads: dict[str, dict[str, float]]) -> None:
        counts = sorted(r["count_ms"] for r in reads.values())
        samples = sorted(r["sample100_ms"] for r in reads.values())
        pages = sorted(r["page200_ms"] for r in reads.values())

        def pct(s: list[float], q: float) -> float:
            return s[max(0, int(len(s) * q) - 1)]

        self.stdout.write(
            f"  Aggregated across {len(reads)} segments — best of 5 each:"
        )
        self.stdout.write(
            f"  {'metric':<14} {'min':>8} {'p50':>8} {'p95':>8} {'max':>8}"
        )
        for label, series in (
            ("count", counts),
            ("sample100", samples),
            ("page200", pages),
        ):
            self.stdout.write(
                f"  {label:<14} {min(series):>8.1f} {pct(series, 0.50):>8.1f} "
                f"{pct(series, 0.95):>8.1f} {max(series):>8.1f}"
            )

    def _print_write_summary(self, write_results: dict[str, dict[str, float]]) -> None:
        self.stdout.write("update_traits write overhead (ms, per call from caller):")
        self.stdout.write(f"  {'phase':<22} {'p50':>8} {'p95':>8} {'mean':>8}")
        ordered = [
            ("disabled", "index disabled"),
            ("sync", "SYNCHRONOUSLY"),
            ("thread", "SEPARATE_THREAD"),
            ("processor_enqueue", "TASK_PROCESSOR (enq)"),
        ]
        baseline = write_results["disabled"]["p50"]
        for key, label in ordered:
            row = write_results[key]
            self.stdout.write(
                f"  {label:<22} {row['p50']:>8.2f} {row['p95']:>8.2f} "
                f"{row['mean']:>8.2f}"
            )
        for key, label in ordered:
            if key == "disabled":
                continue
            delta = write_results[key]["p50"] - baseline
            self.stdout.write(
                f"  {('Δ vs disabled (' + label + ')'):<32} {delta:>+8.2f} ms p50"
            )


# pyflakes: silence unused-import warning for the os import (kept for environment debugging).
_ = os

# Experiments v2 — Prototype Notes

Prototype-only decisions and deferred items that aren't worth putting in
production code but should survive a context handover.

## Deferred: demo URL param for empty metrics

**Context:** the Select Metrics step (`steps/SelectMetricsStep.tsx`) has an
empty state for when the metric catalog is empty — useful for showcasing the
"create your first metric" flow. It's not reachable by default because
`MOCK_METRICS` always has 5 entries, and the wizard's `INITIAL_STATE`
pre-selects three of them.

**Decision:** gate empty-state demo behind a URL param rather than flipping
the default mock. Keeps the happy-path demo intact.

**Proposed param:** `?demoEmptyMetrics=1` on the create-experiment route.
When present:

- Pass `availableMetrics={[]}` to `SelectMetricsStep` (overrides the
  `MOCK_METRICS` default).
- Skip the three pre-selected metrics in `CreateExperimentPage`'s
  `INITIAL_STATE` so `state.metrics` starts empty too.

**Parse via:** `Utils.fromParam()` in `CreateExperimentPage` (same pattern
used elsewhere in the codebase — e.g. `web/main.js`, `IntegrationList.tsx`).

**Why not built yet:** low priority for the current prototype milestone;
designers can still see the empty state via the Storybook story or by
temporarily clearing `MOCK_METRICS`.

## Deferred: sample-size / duration calculator

**Context:** the Segments & Traffic step (`steps/SegmentTrafficStep.tsx`)
currently shows a soft one-liner under the Traffic Split: *"Rough split: ~N
users per arm. Actual sample size and time-to-significance depend on
traffic, baseline rate, and the lift you're trying to detect."*

The earlier prototype showed a fabricated *"Est. 14 days to significance"*
— removed because it had no statistical basis and would set false
expectations.

**What a real implementation needs:**

1. **Segment traffic estimate** — not just "how many identities match this
   segment" but "how many of them hit this flag per day". Options:
   - Cached daily segment counts (nightly cron, stale ≤24h) — cheapest MVP.
   - Historical impressions from a new table tracking flag-evaluation
     events per segment — what LaunchDarkly does. More infra but better
     signal.
2. **Metric baseline rate (`p`)** — e.g. "conversion is 7% today". Either
   the user types it, or we derive from historical metric data (needs a
   metrics warehouse we don't have yet).
3. **Minimum Detectable Effect (MDE) input** — user specifies the smallest
   lift they care about. Dedicated form field in the wizard.
4. **Power calculation** — standard formula for proportion metrics:
   `n_per_arm ≈ 16 × p(1-p) / MDE²`; duration =
   `n_per_arm × arms / daily_traffic`.

**Why not built yet:** real feature, not a polish item. Needs backend
infra for (1) + (2) and a new wizard input for (3). Worth a separate
sprint once the rest of Experiments v2 ships.

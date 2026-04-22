# Experiments v2 — Prototype Notes

Prototype-only decisions and deferred items that aren't worth putting in
production code but should survive a context handover.

## Demo shortcuts

Query-param affordances baked into the prototype for presenting and
screenshotting. None of them are visible in normal usage — no query param,
no demo UI.

### Data Warehouse state shortcuts

Defined in `web/components/warehouse/WarehousePage.tsx`.

- **`?state=<name>`** — jumps directly to a specific connection state
  without clicking through the full flow. Values:
  - `empty` (default)
  - `configuring` — the form with Snowflake / BigQuery / Databricks picker
    and the two-button Test / Connect footer
  - `testing` — the 4-step "Connecting…" animation
  - `connected` — the live-stats + connection-details page
  - `error` — the auth-failed state with retry / edit actions
- **`?demo=1`** — shows an inline state-switcher pill bar above the
  content. Click any pill to switch state live. The bar has a
  warning-tinted dashed border so it reads unmistakably as demo-only.
- Combine them: `?demo=1&state=connected` opens on the connected state
  with the switcher ready for live clicks.

### Experiments empty-metrics shortcut (proposed, not built)

See *Deferred: demo URL param for empty metrics* below.

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

## Design-system note: 1220px rail vs. full-width surfaces

**Context:** every existing Flagsmith page wraps its content in
`<div className='app-container container'>`, which caps at `max-width:
1220px` (see `web/styles/project/_layout.scss:10`). That cap is a legacy
choice sized for ~1280px monitors; on a modern 2560-wide display the
content floats in the centre with ~670px of dead space on each side.

The new Warehouse page is deliberately **not** wrapped in `app-container
container` — it spans the viewport (with sensible padding on
`.warehouse-page`). The stats row, connection-details card, and form all
breathe naturally.

**This is intentional**, not a consistency bug:

- The 1220px rail is design debt from the existing app, not a target.
- Modern SaaS (Linear, Vercel, Stripe, Statsig) lets the outer container
  breathe and constrains inner blocks per-content-type — forms/prose cap
  at 720–800px for readability, tables and dashboards span wider.
- The warehouse page is showing what "right" looks like; the rest of the
  app needs to follow, not the reverse.

**Talking point for the demo:** "Notice how this new surface uses the
full viewport? That's intentional — it's part of the wider design-system
refresh we want to do. The 1220px cap on every other page is on our
audit list (#6606)."

**Follow-up if accepted as a direction:**

- Audit which pages benefit from full-width (usage, analytics, tables,
  dashboards) vs. narrow (settings forms, prose).
- Replace the blanket `app-container` cap with per-page width policies, or
  introduce a `.app-container--wide` / `.app-container--narrow` modifier.
- Track as part of the design-system audit (#6606), not a one-off warehouse
  change.

## Deferred: "Connected" indicator on the Integrations list card

**Context:** the Data Warehouse entry in `integration_data` uses `external:
true` with a same-origin link (`/organisation/:organisationId/warehouse`),
so it renders via `IntegrationList.tsx` lines 144–155 — a plain `<a>` CTA
with no active-integration row beneath. The card looks identical whether or
not a warehouse is connected.

Drawer-based integrations (Datadog, Segment, Slack) show a connected row
via `IntegrationList.tsx` lines 316–354, but that path requires a real
backend endpoint (`GET /organisations/:id/integrations/:key/`) which the
warehouse prototype doesn't have. Other `external: true` integrations
(Jira) have the same gap — it's not specific to us.

**Implication for the demo:** returning users can't tell from the
Integrations list whether they've already set up a warehouse. They have to
click through to the Warehouse page to see connection status. Acceptable
for the prototype; the presentation flow clicks through anyway.

**Two follow-up options if this ships:**

1. **Mock-only:** add `connected?: boolean` to the integration JSON and
   render a green "Connected" pill in the card header. Cheapest, no backend.
2. **Real:** add `GET /organisations/:id/integrations/data-warehouse/`
   returning the stored config, wire `IntegrationList` to fetch it like the
   drawer-based ones. Matches existing infra and gives us a proper active
   row (with Edit / Delete controls inline on the card).

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

## Deferred: guardrail semantic-flip on the results page

**Context:** metric roles (primary / secondary / guardrail) are now rendered
on the Experiment Results page via `MetricsComparisonTable`. Primary and
secondary metrics use the existing lift/significance colouring — positive
lift renders green, negative renders red.

Guardrails should flip this: a **significant regression** on a guardrail
(positive lift on a lower-better metric, negative lift on a higher-better
metric) is a **failure** and should render as danger/warning, not neutral.
Example: page-load-time goes up 8% with p<0.01 — today that'd render as
"positive" because the lift bar only looks at `liftValue`'s sign; it should
render as a red "regression" warning.

**What's needed:**
1. Propagate `MetricDirection` ('higher-better' | 'lower-better' | 'neither')
   from `Metric` onto `MetricComparison` (it stops at the wizard today).
2. Compute "is this a regression?" per metric:
   `role === 'guardrail' && isSignificant && sign(liftValue) !== wantedDirection`.
3. When true, override the lift-bar colour and significance label to a
   danger tone, and consider adding a warning icon in the significance
   column.

**Why not built yet:** demo showed guardrails as a distinct visual category
which is the main UX win; the semantic-flip is a correctness refinement that
needs extra type work and would stretch tomorrow's scope.

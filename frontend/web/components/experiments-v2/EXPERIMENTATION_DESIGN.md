# Experiments v2 — Design Proposal

Presentation notes for the Experiments v2 prototype. Explains the design
choices, how they map onto Flagsmith's data model, and the references that
back each decision.

## Context

Flagsmith already ships multi-variant flags, segment overrides, and identity
targeting — everything you need to run an experiment. What's missing is the
**workflow**: a guided way to set up a controlled experiment, pick metrics,
split traffic, and read results. Experiments v2 fills that gap as a
first-class product concept on top of the existing primitives.

## Scope

This prototype is **frontend-only**. The wizard is fully interactive with
mock data; no backend endpoints, no real metrics pipeline, no statistical
engine. See `NOTES.md` for the deferred items that require backend work
(sample-size calculator, metric baseline data, segment traffic tracking).

The prototype covers:

- Create Experiment wizard (5 steps)
- Experiments list + Metrics library (tabs)
- Experiment results page (comparison table + trend chart)

It does **not** cover:

- Post-launch experiment state management (pause/stop/restart)
- Real sample-size or power calculations
- Historical metric data or baselines
- Randomisation-unit override (we assume identity-based bucketing)

## Vocabulary

The audience of an experiment has three layers, each with its own term.
Segments stay a Flagsmith primitive — they just stop pulling double duty.

| Term we use | What it means | Notes |
|---|---|---|
| **Audience** | The whole step / concept: who's eligible, how many of them are in, and how they split | LD calls this "Audience allocation" |
| **Targeting** (optional **Segment** filter) | Eligibility filter. Users matching the segment are eligible; everyone else is excluded. Empty = all identities in the environment | Segments stay a normal Flagsmith primitive — they just don't define the experiment audience by themselves |
| **Sample size** | Percentage of eligible users actually sampled into the experiment. The rest see the flag's environment default | LD: "Percent of users in this experiment" |
| **Variation split** | Among the sampled users, the per-arm weight distribution. Control takes a slot. Sum to 100 | LD: "Variation split" |
| **Variation** / **Control value** | Variation = an entry in the flag's variation list; control value = a field on the flag itself | Existing Flagsmith concepts |
| **Guardrail metric** | A safety-check role separate from primary/secondary | See [Metric roles](#metric-roles) |

Internally we use `arm` as jargon for "control or variation" when doing
weight math, but user-facing copy stays as "variation".

### Why segments aren't the audience

The earlier prototype used a segment as the experiment's audience: pick
one segment, set per-arm weights, done. That conflated **targeting**
(property-based filter) with **audience allocation** (random sample of
eligible users). Two concrete failure modes:

1. **No segment? No experiment.** Want to A/B test on the whole user
   base? You'd need a fake "All users" segment. Segments are
   property-based, not "everyone".
2. **No way to ramp.** Want to start at 5% and ramp up? You'd need a
   property-based segment that captures 5% of users — segments aren't
   random samplers.

Splitting the concept into three layers (Targeting / Sample size /
Variation split) fixes both: targeting is *optional*, sampling is *its
own knob*, and split is *just the variation distribution*.

## Data model

An experiment is a **first-class record** that holds the audience
configuration plus the variation weights. The audience is layered —
optional segment filter, sample percentage, and per-arm weights — and
each layer has a backend equivalent.

```
Experiment {
  // Audience
  targeting_segment: <segment id> | null   // null = all identities in the environment
  sample_percentage: 0–100                 // fraction of eligible users sampled in
  weights: [
    { value: <control_value>, weight: X },
    { value: <variation_1.value>, weight: Y },
    { value: <variation_2.value>, weight: Z },
  ]                                         // X + Y + Z = 100

  // Forward-designed for later iterations
  outside_variation: <flag default>         // served to eligible-but-not-sampled users
  mutual_exclusion_group: null              // layer ID; null means no exclusion
}
```

**Implications:**

1. **Targeting is optional.** No segment selected = the eligible pool is
   every identity in the environment. This is the default.
2. **Sample size is independent of variation split.** Setting sample_size
   to 10% means 10% of eligible identities are in the experiment, and the
   variation weights split *those* users. The other 90% see the flag's
   environment default.
3. **Weights must sum to 100% across the sampled pool**, including
   control. Control is still a field on the flag, not a variation —
   the wizard treats it as one of the weight slots.
4. **One experiment per (segment, flag) pair.** If the chosen segment
   already has an override on the flag, the wizard shows a conflict
   banner. Existing overrides on other segments are unaffected; priority
   ordering decides who wins for users matching multiple segments.
5. **Assignment requires two hash dimensions.** Hash 1 (`experiment_id +
   identity`) decides "in or out of the experiment". Hash 2
   (`experiment_id + identity` with a salt) decides which variation. This
   keeps "% in experiment" stable when you change the variation split,
   and vice versa.

### Forward-designed fields (`outside_variation`, `mutual_exclusion_group`)

The data model includes two more fields the v1 UI doesn't surface:

| Field | v1 default | When it lights up |
|---|---|---|
| `outside_variation` | flag's environment default | Let teams pick which variation eligible-but-not-sampled users see, decoupled from the flag's default. Useful when the experiment changes the flag default or when ramping without rolling back the default. |
| `mutual_exclusion_group` | `null` | Group experiments into a "layer" so a user is in at most one experiment per layer. Prevents traffic overlap when several experiments target the same audience. |

Both stay inert until the UI exposes them. Including them up front
avoids a future schema migration on a live data model.

## Wizard flow

Five steps, in this order:

1. **Experiment Details** — name, hypothesis (required), start and end dates
2. **Flag & Variations** — pick a multi-variant flag, view its variations (read-only)
3. **Select Metrics** — primary, secondary, guardrail roles
4. **Audience** — optional segment filter, sample size, variation split
5. **Review & Launch** — full summary with edit shortcuts

### Why Details first, not Flag first

Writing the hypothesis before picking the flag forces users to think about
*what they're trying to learn* before getting lost in config. This is the
LaunchDarkly pattern and Kohavi's recommendation in *Trustworthy Online
Controlled Experiments*.

**Counter-argument:** the wizard's shape depends on the flag (variation
count → arm weights), so Flag-first could feel more natural. We went
Details-first for the intent-setting benefit; the downside is users
occasionally edit back when they realise their flag choice changes the arm
count.

### Why variations are read-only

Variations live on the flag, not the experiment. Letting users add or
remove variations from inside the wizard would mutate the flag config
silently. Instead we show the existing variations and block progression if
the flag has fewer than one (the minimum for a two-arm experiment: control
+ one variation).

## Metric roles

We support three roles:

| Role | Purpose | Stat question |
|---|---|---|
| **Primary** | The metric the experiment's verdict is based on | "Did the change improve this?" |
| **Secondary** | Other effects we want to observe | "What else moved?" |
| **Guardrail** | Metrics we must not regress, even if primary wins | "Did anything I care about break?" |

### Why three roles, not two

**Guardrails are a distinct axis** — not a ranking of importance, but a
different question entirely. A guardrail can be a metric that has nothing
to do with what the experiment is testing (e.g. page latency on a checkout
button redesign). Making it a separate role **forces the user to think
about safety**, not just optimisation.

This is the convention in rigorous experimentation platforms:
- **Statsig** — dedicated *Guardrail Metrics* tier
- **Eppo** — first-class guardrail role
- **GrowthBook** — *Guardrail metrics* separate from *Goal metrics*
- **Optimizely** — monitoring/impact metrics serve the same role
- **Airbnb, Netflix, Microsoft ExP** — internal platforms all surface
  guardrails (sometimes called "tripwires" or "health metrics")

LaunchDarkly rolls this into secondary metrics today. We're taking the more
rigorous convention — backed by the industry textbook.

### Soft warning on multi-primary

When a user picks more than one primary metric, we surface a warning about
the multiple-comparisons problem without blocking. Best practice is one
primary; the warning explains why and invites the user to demote the rest.

## Data collection — how metrics get measured

The prototype mocks all metric values, but the architecture question is the
one the demo audience will ask first. Three production-ready approaches,
and what Flagsmith is set up to do.

### Option A — SDK-based event ingestion (what LaunchDarkly does)

Customer calls `flagsmith.track('checkout_completed', { value: 49.99,
identity: userId })` from their app. Flagsmith SDKs ship events to a
collection endpoint. Flagsmith's backend joins each event with the flag
evaluation the user saw (attribution), aggregates per arm, surfaces the
roll-up on the results page.

- **Pros**: simplest onboarding for customers — no external tooling needed.
- **Cons**: biggest backend lift — we'd need an event ingestion service,
  time-series storage, attribution pipeline, and aggregation. Doable on top
  of the existing Edge/Task Processor infrastructure.

### Option B — Warehouse-native (what this prototype shows)

Events already live in the customer's data warehouse (Snowflake, BigQuery,
Databricks). Customer defines a metric by pointing Flagsmith at a warehouse
table + event name (or value column) + optional filter. Flagsmith pushes
flag-evaluation records into the same warehouse and runs aggregation
queries to compute per-arm results.

This is the path shown in the current mocks:
- `web/components/warehouse/WarehousePage.tsx` — connection config
  (Snowflake live; BigQuery/Databricks marked "Coming Soon")
- `ConnectionStats` mock shows `flagEvaluations24h: 1.28M` +
  `customEvents24h: 84K` flowing into the connected warehouse
- Metric Library's `CreateMetricForm` includes a **Data Source** section
  mapping each metric to `{warehouse, table, eventName | valueColumn,
  filter}`
- Each mock metric in `MOCK_METRICS` carries a `source` that renders
  inline in the library (e.g. *"EVENTS · checkout_completed"*)

**Pros**: cheapest for Flagsmith to build — the customer's warehouse does
the heavy aggregation. Customer owns their data.

**Cons**: requires the customer to have a warehouse. Not viable for
smaller customers running SaaS without a data pipeline.

**Competitors that ship this model**: Eppo (primary), GrowthBook
Enterprise, Statsig (warehouse mode).

### Option C — Analytics tool integration

Metric definition lives in the customer's existing analytics tool (Segment,
Amplitude, Mixpanel, Heap, Google Analytics). Flagsmith pulls aggregates
via those tools' APIs and attributes by variation.

- **Pros**: leverages what customers already use; fastest to value for
  teams that have analytics but not a warehouse.
- **Cons**: every tool's API is different; rate limits, latency, and
  attribution edge cases multiply per integration.

### What the prototype demonstrates

This build-out shows **Option B (warehouse-native)** end-to-end as mock UI:

1. `Data Warehouse` page under the organisation nav — confirm the
   connection is live, see stats on event throughput
2. `Metrics` library — each metric shows its source mapping
   (`EVENTS · checkout_completed`, `TRANSACTIONS · amount_usd WHERE
   status = 'complete'`, etc.)
3. Create / Edit Metric — a **Data Source** section maps the metric to the
   warehouse table + event/column + optional filter
4. Experiment Results — per-arm numbers that (in production) would come
   from aggregation queries against the warehouse

### Recommended sequencing

If this were going from prototype to production:

1. **First**: ship warehouse-native (Option B) — lowest infra risk, serves
   the experimentation-mature segment. The mocks in this repo are a
   working starting point.
2. **Then**: add SDK `track()` (Option A) so customers without a warehouse
   can still run experiments. Reuses the existing SDK analytics pipeline.
3. **Later**: selective analytics integrations (Option C) — Segment first
   because it's the universal fanout layer for the others.

Captured separately in `NOTES.md`: the **sample-size calculator** and
**guardrail semantic-flip** both depend on the collection pipeline above
being real — they're the reason this section exists as design intent, not
just a demo touch.

## Traffic split mechanics

Weights are edited via number inputs (0–100 each). When a user changes one
arm, the remaining weight is **redistributed proportionally** across the
others so the sum always lands on exactly 100.

- With 2 arms: trivial — the other arm gets `100 − new`.
- With 3+ arms: delta is distributed proportionally based on current
  weights, preserving the ratio between the unchanged arms.
- Integer rounding: a largest-fractional-part pass ensures the sum is
  always exactly 100, never 99 or 101.

An arm at 0 stays at 0 during rebalancing (a zero-weight arm is "excluded
by intent"). Users hit **Split evenly** to reset.

## Safety & conflict detection

- **Conflict banner** — when the selected segment already has an override
  on the target flag, we surface a red banner directly under the segment
  dropdown with resolution paths ("pick a different segment, or remove the
  existing override on the Features page first").
- **Guardrail metrics** — see above.
- **Launch confirmation modal** — no accidental launches. The modal names
  both the flag and segment explicitly.

## Presentation walkthrough

Suggested narrative order for the live demo. Every step below has a
matching URL or shortcut so you don't have to click through the full
flow when you want to land on a specific state.

### 1 — Frame the problem (30s)

Open `/project/:id/environment/:id/experiments` (empty-ish or with mock
list). Motivate: Flagsmith has flags, segments, and identity targeting
— everything to *run* an experiment, but no workflow to *set one up*.
This branch adds that.

### 2 — Data collection story (45s)

Open **Organisation Integrations** → show the **Data Warehouse** card
alongside Jira, Grafana, etc. Click **Add Integration**.

Use `?demo=1&state=empty` on the warehouse URL for the first landing.
Then cycle the switcher to narrate:

- **Empty** → "no warehouse connected"
- **Configuring** → the connection form, call out the two-button Test
  / Connect pattern (Test = verify only; Connect = commit)
- **Testing** → the 4-step Connecting animation
- **Connected** → live-stats card with 24h flag evaluations + custom
  events flowing through, connection details grid
- **Error** → the auth-failed state with resolution paths

Anchor: *"this is where experiment metrics come from — the warehouse
does the aggregation, Flagsmith reads the result."* Pair with the
three-approach framing from the Data collection section above.

### 3 — Metrics library (45s)

Back to the experiments nav → **Metrics**. Point out:

- Each metric shows its warehouse source inline (`EVENTS ·
  checkout_completed`, `TRANSACTIONS · amount_usd WHERE status =
  'complete'`, etc.) — the direct handoff from the warehouse story
- Role system (primary / secondary / guardrail) — highlight this is
  where Flagsmith differs from LaunchDarkly
- Create Metric → walk through measurement type cards, direction
  picker, data source section

### 4 — Create Experiment wizard (90s)

From the Experiments list, **Create Experiment**. Walk the 5 steps:

1. **Details** — name, hypothesis (required, with a real-example
   placeholder), default dates (+14 days from today)
2. **Flag** — multi-variant flag picker; read-only variations table.
   Optional detour: pick `homepage_hero_redesign` (0 variations) to
   show the blocking banner
3. **Metrics** — pre-selected Conversion Rate (primary) + Revenue per
   User (secondary) + Page Load Time (guardrail). Click one to show
   the three-role segmented control. Add a second primary to surface
   the soft multi-primary warning
4. **Audience** — three sub-blocks: Targeting (leave empty for "all
   users", or pick Premium Tier on flag-1 to trigger the inline
   conflict banner), Sample size (toggle 100 → 10 to show the dial
   independently from the variation split), Variation split (play
   with the auto-balancing weights — change one, watch the others
   rebalance proportionally)
5. **Review & Launch** — full summary with per-section edit links.
   Click **Launch** → confirmation modal → toast + redirect to list

### 5 — Results page (45s)

From the list, click a running experiment. Narrate top-down:

- Stat cards + recommendation callout
- Metrics comparison table — call out the primary-row emphasis,
  guardrail badge, zero-centred lift bars
- Scroll to the trend chart — metric selector + control vs treatment
  line chart

Anchor: *"this is the loop closed — metrics defined in the library,
data streaming through the warehouse, results computed per arm."*

### 6 — What's deferred (30s)

Short list from the *What we're deferring* section. Keep it honest —
this is a workflow prototype, not a production experimentation
platform. Backend work is the next sprint.

## What we're deferring

Captured in `NOTES.md`:

- **Sample-size / duration calculator** — needs backend infra (cached
  segment counts + metric baseline data) and a new MDE input
- **Demo URL param for empty metrics** — for showcasing the empty state
  without clearing the mock catalog

Not yet captured but known gaps:

- Post-launch experiment management (pause, stop, re-launch)
- Flag collision detection (flag already has a running experiment)
- Randomisation unit selector (currently assumes identity-based)
- Save-as-draft
- Test-identity preview ("would user X be in this experiment?")

## References

### Academic / industry

- Kohavi, R., Tang, D., & Xu, Y. (2020). *Trustworthy Online Controlled
  Experiments: A Practical Guide to A/B Testing.* Cambridge University
  Press. **Chapter 7 covers guardrail metrics explicitly.** This is the
  definitive industry textbook.
- Kohavi, R. et al. (2019). *Top Challenges from the first Practical Online
  Controlled Experiments Summit.* SIGKDD. Documents shared practices
  across Airbnb, Amazon, Google, LinkedIn, Microsoft, Netflix.
- Kohavi, R. & Thomke, S. (2017). *The Surprising Power of Online
  Experiments.* Harvard Business Review.

### Vendor documentation

- **Statsig** — Guardrail Metrics as a dedicated metric tier
- **Eppo** — Guardrail metrics as a first-class role
- **GrowthBook** — open source; guardrails separate from goal metrics
- **Optimizely** — impact / monitoring metrics serve the same role
- **LaunchDarkly** — health metrics are informal, not a distinct UI role
  today (gap Flagsmith can close)

### Engineering blogs

- Netflix Tech Blog — multiple posts on the XP experimentation platform,
  including guardrails for streaming quality and error rates
- Airbnb Engineering — ERF (Experimentation Reporting Framework) papers
  mention guardrail/tripwire metrics
- Booking.com — experimentation culture posts calling out guardrails for
  revenue metrics

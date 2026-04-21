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

We chose Flagsmith-native terms wherever the concept exists. Where we
borrowed, we say so.

| Term we use | Alternative (LD) | Why |
|---|---|---|
| **Segment** | Audience | `Segment` is a real Flagsmith data model; `Audience` isn't anywhere else in the product |
| **Variation** | Variation / Arm | Matches the existing flag field name |
| **Control value** | Variation | In Flagsmith's model, control is a **field on the flag**, not an entry in the variations list |
| **Traffic split** | Allocation | Common term across all vendors |
| **Guardrail metric** | Secondary / Health | Distinct role — see [Metric roles](#metric-roles) |

Internally we use `arm` as jargon for "control or variation" when doing
weight math, but user-facing copy stays as "variation".

## Data model

An experiment in Flagsmith is a **segment override with weights on a
multi-variant flag**. Specifically:

```
FeatureSegment {
  segment: <your target segment>
  priority: <assigned automatically>
  weights: [
    { value: <control_value>, weight: X },
    { value: <variation_1.value>, weight: Y },
    { value: <variation_2.value>, weight: Z },
  ]  // X + Y + Z = 100
}
```

**Implications:**

1. An experiment targets **one segment**. Users outside that segment hit the
   flag's environment default, not the experiment.
2. Weights must sum to 100% across **all values** of the flag — including
   control. You can't have a split that only touches the variations; users
   matching the segment have to be assigned somewhere.
3. Two overrides on the same segment **cannot coexist**. This is why the
   wizard shows a blocking conflict banner when the selected segment already
   has an override on the target flag.
4. Existing segment overrides on other segments are unaffected. Priority
   ordering decides who wins for users matching multiple segments.

## Wizard flow

Five steps, in this order:

1. **Experiment Details** — name, hypothesis (required), start and end dates
2. **Flag & Variations** — pick a multi-variant flag, view its variations (read-only)
3. **Select Metrics** — primary, secondary, guardrail roles
4. **Segments & Traffic** — target segment + per-arm weights
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
